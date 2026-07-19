---
name: sync-skills
description: Reconcile the skills repo (Canonical Source) with ~/.agents/skills (Installed Set) — install, adopt, remove, or sync skills and resolve drift conflicts.
metadata:
  origin: gauthiermartin/skills
  origin-status: local
disable-model-invocation: true
---

# Sync Skills

Every operation is a thin wrapper over `scripts/skills-sync.py` in the Canonical Source repo (`~/Developer/Repositories/skills`) — the deterministic engine defined by `CONTEXT.md` and ADR 0001. Run it with `uv run`; never reimplement its logic with ad-hoc copying.

## Operations

All commands run from the repo root. Names come from `status`; never guess.

- **Status** — `uv run scripts/skills-sync.py status --json` — per-skill state: `synced`, `not-installed`, `removed`, `repo-ahead`, `installed-ahead`, `conflict`, `repo-deleted`, `missing`, `foreign`, `unrecorded`.
- **Sync** — `uv run scripts/skills-sync.py sync` — one-sided changes flow automatically; exits 2 when conflicts remain.
- **Install / Remove** — `... install <name>` / `... remove <name>` — add a Canonical skill to the Installed Set, or deliberately remove it (recorded; sync never resurrects it).
- **Adopt** — `... adopt <name>` — capture a `foreign` (installed-only) skill into the Canonical Source. Follow up by committing the new `skills/<name>/` with a provenance `metadata:` block.
- **Conflicts** — show `... diff <name>` to the user, then apply their choice with `... accept repo|installed <name>`. Never pick a side for them.

## Rules

- A `repo-deleted` conflict means the skill was removed from the repo but is still installed — surface it; the user decides between `accept repo` (delete locally) and `accept installed` (re-adopt).
- After `sync` copies changes INTO the repo (`installed → repo`), the repo has uncommitted changes — offer to ship them.
- The TUI (`uv run scripts/skills-sync.py` with no arguments) is for humans at a terminal; agents use the flag commands above.
