#!/usr/bin/env python3
"""Reset GitHub labels from a preset, using the gh CLI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

COLOR = re.compile(r"^[0-9a-fA-F]{6}$")


def load_preset(path: Path) -> tuple[str, list[dict[str, str]]]:
    data = json.loads(path.read_text())
    name = data.get("name")
    labels = data.get("labels")
    if not isinstance(name, str) or not name:
        raise SystemExit(f"{path}: missing string field 'name'")
    if not isinstance(labels, list) or not labels:
        raise SystemExit(f"{path}: missing non-empty list field 'labels'")

    seen_names: set[str] = set()
    seen_colors: set[str] = set()
    for i, label in enumerate(labels, 1):
        for field in ("name", "color", "description"):
            if not isinstance(label.get(field), str) or not label[field].strip():
                raise SystemExit(f"{path}: label {i} missing string field {field!r}")
        label["color"] = label["color"].lstrip("#").lower()
        lowered_name = label["name"].lower()
        if lowered_name in seen_names:
            raise SystemExit(f"{path}: duplicate label name {label['name']!r}")
        if label["color"] in seen_colors:
            raise SystemExit(f"{path}: duplicate color {label['color']}")
        if not COLOR.fullmatch(label["color"]):
            raise SystemExit(f"{path}: invalid color {label['color']!r}")
        seen_names.add(lowered_name)
        seen_colors.add(label["color"])
    return name, labels


def gh(*args: str) -> str:
    proc = subprocess.run(
        ["gh", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout.strip()


def resolve_repo(repo: str | None) -> str:
    return repo or gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")


def current_label_names(repo: str) -> list[str]:
    out = gh("label", "list", "--repo", repo, "--limit", "1000", "--json", "name", "--jq", ".[].name")
    return [line for line in out.splitlines() if line]


def current_labels(repo: str) -> dict[str, dict[str, str]]:
    out = gh("label", "list", "--repo", repo, "--limit", "1000", "--json", "name,color,description")
    labels = json.loads(out or "[]")
    return {label["name"].lower(): label for label in labels}


def apply(repo: str, preset_name: str, labels: list[dict[str, str]], confirm: str | None) -> None:
    expected = f"reset labels in {repo} with {preset_name}"
    if confirm != expected:
        raise SystemExit(f"Refusing destructive reset. Re-run with --confirm {expected!r}")

    for name in current_label_names(repo):
        print(f"delete {name}")
        gh("label", "delete", name, "--repo", repo, "--yes")

    for label in labels:
        print(f"create {label['name']}")
        gh(
            "label",
            "create",
            label["name"],
            "--repo",
            repo,
            "--color",
            label["color"],
            "--description",
            label["description"],
        )

    actual = current_labels(repo)
    expected_labels = {label["name"].lower(): label for label in labels}
    problems: list[str] = []
    if set(actual) != set(expected_labels):
        problems.append(f"names differ: expected {sorted(expected_labels)}, got {sorted(actual)}")
    for key, label in expected_labels.items():
        if key in actual:
            if actual[key]["color"].lower() != label["color"]:
                problems.append(f"{label['name']}: color {actual[key]['color']} != {label['color']}")
            if actual[key].get("description", "") != label["description"]:
                problems.append(f"{label['name']}: description mismatch")
    if problems:
        raise SystemExit("Verification failed:\n" + "\n".join(problems))


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset GitHub labels from a JSON preset using gh.")
    parser.add_argument("--preset", required=True, type=Path, help="Preset JSON file")
    parser.add_argument("--repo", help="owner/repo; defaults to the current gh repository")
    parser.add_argument("--apply", action="store_true", help="Delete existing labels and create the preset")
    parser.add_argument("--confirm", help="Required exact confirmation: reset labels in OWNER/REPO with PRESET")
    parser.add_argument("--validate-only", action="store_true", help="Validate preset JSON without calling gh")
    args = parser.parse_args()

    preset_name, labels = load_preset(args.preset)
    if args.validate_only:
        print(f"{args.preset}: {len(labels)} labels OK; colors unique")
        return

    repo = resolve_repo(args.repo)
    existing = current_label_names(repo)
    if not args.apply:
        print(f"Preset: {preset_name}")
        print(f"Repository: {repo}")
        print(f"Would delete {len(existing)} existing labels and create {len(labels)} labels.")
        print(f"Apply with: --apply --confirm 'reset labels in {repo} with {preset_name}'")
        return

    apply(repo, preset_name, labels, args.confirm)
    print(f"Reset {repo} to preset {preset_name}: {len(labels)} labels verified.")


if __name__ == "__main__":
    main()
