#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["textual>=0.80"]
# ///
"""skills-sync: reconcile the Canonical Source (repo) with the Installed Set.

Vocabulary per CONTEXT.md, design per docs/adr/0001-copies-plus-sync-over-symlinks.md.

Human use:   uv run scripts/skills-sync.py            (Textual TUI)
Agent use:   uv run scripts/skills-sync.py status --json | install NAME | adopt NAME |
             remove NAME | sync | accept repo|installed NAME | diff NAME |
             cutover [--apply] | selfcheck
"""

from __future__ import annotations

import argparse
import re
import difflib
import hashlib
import json
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

IGNORE = {".DS_Store", "__pycache__", ".sync-manifest.json"}

# ---------------------------------------------------------------- hashing

def iter_files(skill_dir: Path):
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file() and not any(part in IGNORE for part in p.relative_to(skill_dir).parts):
            yield p


def skill_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    for p in iter_files(skill_dir):
        h.update(str(p.relative_to(skill_dir)).encode())
        h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

# ---------------------------------------------------------------- manifest

def load_manifest(target: Path) -> dict:
    mf = target / ".sync-manifest.json"
    if mf.exists():
        return json.loads(mf.read_text())
    return {"version": 1, "skills": {}}


def save_manifest(target: Path, manifest: dict) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / ".sync-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

# ---------------------------------------------------------------- scanning

@dataclass
class Row:
    name: str
    status: str  # synced | not-installed | removed | repo-ahead | installed-ahead |
    #              conflict | repo-deleted | missing | foreign | unrecorded
    repo_hash: str | None
    inst_hash: str | None


def list_skills(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    out = {}
    for p in sorted(root.iterdir()):
        if p.name.startswith(".") or p.name in IGNORE:
            continue
        if p.is_dir() and (p / "SKILL.md").exists():
            out[p.name] = p
    return out


def scan(repo: Path, target: Path, manifest: dict) -> list[Row]:
    repo_skills = list_skills(repo)
    inst_skills = list_skills(target)
    names = sorted(set(repo_skills) | set(inst_skills) | set(manifest["skills"]))
    rows = []
    for name in names:
        r = skill_hash(repo_skills[name]) if name in repo_skills else None
        i = skill_hash(inst_skills[name]) if name in inst_skills else None
        entry = manifest["skills"].get(name)
        state = entry["state"] if entry else None
        base = entry.get("hash") if entry else None

        if state == "installed":
            if r is None and i is None:
                status = "repo-deleted"  # gone everywhere; resolve drops entry
            elif r is None:
                status = "repo-deleted"
            elif i is None:
                status = "missing"
            elif r == i:
                status = "synced"
            elif i == base:
                status = "repo-ahead"
            elif r == base:
                status = "installed-ahead"
            else:
                status = "conflict"
        else:  # no entry, or state == removed
            if r and i:
                status = "unrecorded" if r == i else "conflict"
            elif r and not i:
                status = "removed" if state == "removed" else "not-installed"
            elif i and not r:
                status = "foreign"
            else:
                continue  # stale removed entry with nothing on disk
        rows.append(Row(name, status, r, i))
    return rows

# ---------------------------------------------------------------- operations

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def check_name(name: str) -> str:
    """Reject anything that could escape the skills roots (separators, .., dotfiles)."""
    if not NAME_RE.fullmatch(name) or ".." in name:
        raise SystemExit(f"invalid skill name: {name!r}")
    return name

def copy_skill(src: Path, dst: Path) -> None:
    if not (src.is_dir() and (src / "SKILL.md").exists()):
        raise SystemExit(f"not a skill directory: {src}")  # BEFORE touching dst
    if dst.is_symlink() or dst.exists():
        dst.unlink() if dst.is_symlink() else shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*IGNORE))


class Engine:
    def __init__(self, repo: Path, target: Path):
        self.repo, self.target = repo, target
        self.manifest = load_manifest(target)

    def rows(self) -> list[Row]:
        return scan(self.repo, self.target, self.manifest)

    def _record(self, name: str) -> None:
        self.manifest["skills"][name] = {"state": "installed", "hash": skill_hash(self.target / name)}
        save_manifest(self.target, self.manifest)

    def install(self, name: str) -> None:
        check_name(name)
        copy_skill(self.repo / name, self.target / name)
        self._record(name)

    def remove(self, name: str) -> None:
        check_name(name)
        d = self.target / name
        if d.is_symlink():
            d.unlink()
        elif d.exists():
            shutil.rmtree(d)
        self.manifest["skills"][name] = {"state": "removed"}
        save_manifest(self.target, self.manifest)

    def adopt(self, name: str) -> None:
        check_name(name)
        copy_skill(self.target / name, self.repo / name)
        self._record(name)

    def accept(self, side: str, name: str) -> None:
        check_name(name)
        row = next((x for x in self.rows() if x.name == name), None)
        if row is None:
            raise SystemExit(f"unknown skill: {name}")
        if side == "repo":
            if row.repo_hash is None:  # repo-deleted: accept the deletion
                self.remove(name)
                del self.manifest["skills"][name]
                save_manifest(self.target, self.manifest)
            else:
                self.install(name)
        elif side == "installed":
            if row.inst_hash is None:  # missing locally: accept the local deletion
                self.manifest["skills"][name] = {"state": "removed"}
                save_manifest(self.target, self.manifest)
            else:
                self.adopt(name)
        else:
            raise SystemExit("side must be 'repo' or 'installed'")

    def sync(self) -> tuple[list[str], list[Row]]:
        """Auto-flow one-sided changes; return (actions, conflicts)."""
        actions, conflicts = [], []
        for row in self.rows():
            if row.status == "repo-ahead":
                self.install(row.name)
                actions.append(f"repo → installed: {row.name}")
            elif row.status == "installed-ahead":
                self.adopt(row.name)
                actions.append(f"installed → repo: {row.name}")
            elif row.status in ("synced", "unrecorded"):
                if self.manifest["skills"].get(row.name, {}).get("hash") != row.inst_hash:
                    self._record(row.name)
                    if row.status == "unrecorded":
                        actions.append(f"recorded: {row.name}")
            elif row.status in ("conflict", "repo-deleted", "missing", "foreign"):
                conflicts.append(row)
        return actions, conflicts

    def diff(self, name: str) -> str:
        check_name(name)
        a_dir, b_dir = self.repo / name, self.target / name
        a_files = {str(p.relative_to(a_dir)): p for p in iter_files(a_dir)} if a_dir.is_dir() else {}
        b_files = {str(p.relative_to(b_dir)): p for p in iter_files(b_dir)} if b_dir.is_dir() else {}
        out = []
        for rel in sorted(set(a_files) | set(b_files)):
            a = a_files.get(rel).read_text(errors="replace").splitlines() if rel in a_files else []
            b = b_files.get(rel).read_text(errors="replace").splitlines() if rel in b_files else []
            if a != b:
                out += difflib.unified_diff(a, b, f"repo/{name}/{rel}", f"installed/{name}/{rel}", lineterm="")
        return "\n".join(out) or "(no content difference)"

    # ------------------------------------------------------------ cutover

    def cutover(self, claude: Path, apply: bool) -> list[str]:
        """Migrate symlink-era layout: symlinks in target become copies, the
        agent surface becomes one dir-level symlink. Dry-run unless apply."""
        plan: list[str] = []
        handled: set[str] = set()
        # 1 — installed set: symlinks → copies
        if self.target.is_dir():
            for p in sorted(self.target.iterdir()):
                if not p.is_symlink():
                    continue
                real = p.resolve()
                if real.is_dir() and (real / "SKILL.md").exists():
                    plan.append(f"copy   {p.name}  (replace symlink with copy of {real})")
                    handled.add(p.name)
                    if apply:
                        copy_skill(real, p)  # copy_skill unlinks the symlink first
                        self._record(p.name)
                else:
                    plan.append(f"drop   {p.name}  (dangling symlink → {real})")
                    if apply:
                        p.unlink()
        # 2 — record any real dirs not yet in the manifest
        for name in list_skills(self.target):
            if name not in self.manifest["skills"] and name not in handled:
                plan.append(f"record {name}")
                if apply:
                    self._record(name)
        # 3 — agent surface: guard, backup, then one dir-level symlink
        if claude.is_symlink():
            plan.append(f"skip   {claude} (already a symlink → {claude.resolve()})")
        elif claude.is_dir():
            stranded = [n for n, p in list_skills(claude).items()
                        if not p.is_symlink() and not (self.repo / n).is_dir()]
            if stranded:
                plan.append(f"REFUSE {claude}: unadopted local skills would be stranded: {', '.join(stranded)}")
            else:
                bak = claude.with_name(f"skills.bak-{time.strftime('%Y%m%d-%H%M%S')}")
                plan.append(f"backup {claude} → {bak}")
                plan.append(f"link   {claude} → {self.target}")
                if apply:
                    claude.rename(bak)
                    claude.symlink_to(self.target)
        if not apply:
            plan.append("(dry-run: re-run with --apply to execute)")
        return plan

# ---------------------------------------------------------------- TUI

def run_tui(engine: Engine) -> None:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.widgets import DataTable, Footer, Header, RichLog

    BADGE = {
        "synced": "✓ synced", "not-installed": "· not installed", "removed": "− removed",
        "repo-ahead": "↓ repo ahead", "installed-ahead": "↑ installed ahead",
        "conflict": "⚡ conflict", "repo-deleted": "⚡ deleted in repo",
        "missing": "⚡ missing locally", "foreign": "? foreign", "unrecorded": "· unrecorded",
    }

    class SyncApp(App):
        TITLE = "skills-sync"
        CSS = "RichLog { height: 40%; border-top: solid $accent; }"
        BINDINGS = [
            Binding("space", "toggle", "install/remove"),
            Binding("a", "adopt", "adopt"),
            Binding("s", "sync", "sync"),
            Binding("r", "accept_repo", "accept repo"),
            Binding("i", "accept_installed", "accept installed"),
            Binding("d", "diff", "diff"),
            Binding("q", "quit", "quit"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield DataTable(cursor_type="row")
            yield RichLog(wrap=False, highlight=True)
            yield Footer()

        def on_mount(self) -> None:
            t = self.query_one(DataTable)
            t.add_columns("skill", "status")
            self.refresh_rows()

        def refresh_rows(self) -> None:
            t = self.query_one(DataTable)
            t.clear()
            for row in engine.rows():
                t.add_row(row.name, BADGE.get(row.status, row.status), key=row.name)

        def selected(self) -> str | None:
            t = self.query_one(DataTable)
            if t.row_count == 0:
                return None
            return t.get_row_at(t.cursor_row)[0]

        def log_line(self, msg: str) -> None:
            self.query_one(RichLog).write(msg)

        def guarded(self, fn, *a) -> bool:
            """Engine ops raise SystemExit on bad input; log instead of dying."""
            try:
                fn(*a)
                return True
            except SystemExit as e:
                self.log_line(str(e))
                return False

        def action_toggle(self) -> None:
            name = self.selected()
            if not name:
                return
            row = next(x for x in engine.rows() if x.name == name)
            if row.status in ("not-installed", "removed"):
                if self.guarded(engine.install, name):
                    self.log_line(f"installed {name}")
            elif row.status in ("synced", "unrecorded"):
                if self.guarded(engine.remove, name):
                    self.log_line(f"removed {name}")
            else:
                self.log_line(f"{name}: resolve its {row.status} state first (r/i/a)")
            self.refresh_rows()

        def action_adopt(self) -> None:
            name = self.selected()
            if not name:
                return
            if not (engine.target / name).is_dir():
                self.log_line(f"{name}: nothing installed to adopt")
                return
            if self.guarded(engine.adopt, name):
                self.log_line(f"adopted {name} into repo")
            self.refresh_rows()

        def action_sync(self) -> None:
            try:
                actions, conflicts = engine.sync()
            except SystemExit as e:
                self.log_line(str(e))
                return
            for a in actions:
                self.log_line(a)
            for c in conflicts:
                self.log_line(f"⚡ {c.name}: {c.status} — d to diff, r/i to resolve")
            if not actions and not conflicts:
                self.log_line("everything in sync")
            self.refresh_rows()

        def _accept(self, side: str) -> None:
            name = self.selected()
            if name:
                if self.guarded(engine.accept, side, name):
                    self.log_line(f"{name}: accepted {side}")
                self.refresh_rows()

        def action_accept_repo(self) -> None:
            self._accept("repo")

        def action_accept_installed(self) -> None:
            self._accept("installed")

        def action_diff(self) -> None:
            name = self.selected()
            if name:
                self.query_one(RichLog).write(engine.diff(name))

    SyncApp().run()

# ---------------------------------------------------------------- selfcheck

def selfcheck() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo, target, claude = root / "repo", root / "installed", root / "claude"
        (repo / "alpha").mkdir(parents=True)
        (repo / "alpha" / "SKILL.md").write_text("v1\n")
        eng = Engine(repo, target)

        # install
        eng.install("alpha")
        assert (target / "alpha" / "SKILL.md").read_text() == "v1\n"
        assert eng.rows()[0].status == "synced"

        # installed-ahead → sync flows installed → repo
        (target / "alpha" / "SKILL.md").write_text("v2-local\n")
        assert eng.rows()[0].status == "installed-ahead"
        actions, conflicts = eng.sync()
        assert actions and not conflicts
        assert (repo / "alpha" / "SKILL.md").read_text() == "v2-local\n"

        # repo-ahead → sync flows repo → installed
        (repo / "alpha" / "SKILL.md").write_text("v3-repo\n")
        actions, conflicts = eng.sync()
        assert (target / "alpha" / "SKILL.md").read_text() == "v3-repo\n"

        # both sides diverge → conflict; accept repo
        (repo / "alpha" / "SKILL.md").write_text("v4-repo\n")
        (target / "alpha" / "SKILL.md").write_text("v4-local\n")
        assert eng.rows()[0].status == "conflict"
        assert "v4-repo" in eng.diff("alpha") and "v4-local" in eng.diff("alpha")
        eng.accept("repo", "alpha")
        assert (target / "alpha" / "SKILL.md").read_text() == "v4-repo\n"

        # deliberate removal is not resurrection bait
        eng.remove("alpha")
        assert eng.rows()[0].status == "removed"
        _, conflicts = eng.sync()
        assert not (target / "alpha").exists() and not conflicts

        # repo-deleted surfaces as conflict, never silent removal
        eng.install("alpha")
        shutil.rmtree(repo / "alpha")
        assert eng.rows()[0].status == "repo-deleted"
        _, conflicts = eng.sync()
        assert conflicts and (target / "alpha").exists()
        eng.accept("installed", "alpha")  # re-adopt into repo
        assert (repo / "alpha" / "SKILL.md").exists()

        # foreign skill (installed only) surfaces; adopt captures it
        (target / "beta").mkdir()
        (target / "beta" / "SKILL.md").write_text("local-only\n")
        assert {r.name: r.status for r in eng.rows()}["beta"] == "foreign"
        # install of a foreign-only name must fail WITHOUT deleting the installed copy
        try:
            eng.install("beta")
            raise AssertionError("install of repo-missing skill should fail")
        except SystemExit:
            pass
        assert (target / "beta" / "SKILL.md").read_text() == "local-only\n"
        # adopt of a repo-only name must fail without touching the repo copy
        try:
            eng.adopt("alpha-nowhere")
            raise AssertionError("adopt of uninstalled skill should fail")
        except SystemExit:
            pass
        eng.adopt("beta")
        assert (repo / "beta" / "SKILL.md").exists()

        # cutover: symlink → copy, dangling dropped, surface becomes dir symlink
        (repo / "gamma").mkdir()
        (repo / "gamma" / "SKILL.md").write_text("g\n")
        (target / "gamma").symlink_to(repo / "gamma")
        (target / "dangler").symlink_to(root / "nowhere")
        claude.mkdir()
        (claude / "alpha").symlink_to(target / "alpha")
        plan = eng.cutover(claude, apply=False)
        assert any("dry-run" in p for p in plan) and (target / "gamma").is_symlink()
        eng.cutover(claude, apply=True)
        assert not (target / "gamma").is_symlink() and (target / "gamma" / "SKILL.md").exists()
        assert not (target / "dangler").exists()
        assert claude.is_symlink() and claude.resolve() == target.resolve()
        assert list(root.glob("skills.bak-*")) or list(claude.parent.glob("skills.bak-*"))

    print("selfcheck: PASS")

# ---------------------------------------------------------------- CLI

def main() -> None:
    default_repo = Path(__file__).resolve().parent.parent / "skills"
    ap = argparse.ArgumentParser(prog="skills-sync")
    ap.add_argument("--repo", type=Path, default=default_repo)
    ap.add_argument("--target", type=Path, default=Path.home() / ".agents" / "skills")
    ap.add_argument("--claude", type=Path, default=Path.home() / ".claude" / "skills")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("status"); s.add_argument("--json", action="store_true")
    for c in ("install", "remove", "adopt"):
        sub.add_parser(c).add_argument("names", nargs="+")
    sub.add_parser("sync")
    a = sub.add_parser("accept"); a.add_argument("side", choices=["repo", "installed"]); a.add_argument("names", nargs="+")
    sub.add_parser("diff").add_argument("name")
    c = sub.add_parser("cutover"); c.add_argument("--apply", action="store_true")
    sub.add_parser("selfcheck")
    sub.add_parser("tui")
    args = ap.parse_args()

    if args.cmd == "selfcheck":
        selfcheck()
        return
    eng = Engine(args.repo, args.target)
    if args.cmd is None or args.cmd == "tui":
        if args.cmd is None and not sys.stdout.isatty():
            ap.error("no command; use status/install/sync/... in non-interactive mode")
        run_tui(eng)
    elif args.cmd == "status":
        rows = eng.rows()
        if args.json:
            print(json.dumps([row.__dict__ for row in rows], indent=2))
        else:
            for row in rows:
                print(f"{row.status:>16}  {row.name}")
    elif args.cmd in ("install", "remove", "adopt"):
        for n in args.names:
            getattr(eng, args.cmd)(n)
            print(f"{args.cmd}: {n}")
    elif args.cmd == "sync":
        actions, conflicts = eng.sync()
        for x in actions:
            print(x)
        for row in conflicts:
            print(f"CONFLICT {row.name} ({row.status}) — resolve with: accept repo|installed {row.name}")
        if conflicts:
            sys.exit(2)
    elif args.cmd == "accept":
        for n in args.names:
            eng.accept(args.side, n)
            print(f"accepted {args.side}: {n}")
    elif args.cmd == "diff":
        print(eng.diff(args.name))
    elif args.cmd == "cutover":
        for line in eng.cutover(args.claude, args.apply):
            print(line)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
