---
name: anvil-github-reset-labels
description: Reset a GitHub repository's labels to the confirmed engineering preset using gh.
disable-model-invocation: true
---

A label reset replaces every existing GitHub label with the engineering preset. The scheme follows Dave Lunny's sane-labels split: `Status:*` says where work is, `Type:*` says what work is, `Priority:*` says urgency, and `Area:*` says engineering ownership.

This is destructive: deleting a label removes it from every issue and pull request. No label is deleted until the repository and preset are confirmed explicitly.

## 1 — Repository

Resolve the target repository:

```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
```

Use `--repo <owner>/<repo>` when the user names a repository outside the current checkout. Check authentication with `gh auth status` if any `gh` command fails for auth.

**Done when** the target is an `owner/repo` string and `gh` can read its labels.

## 2 — Preset

Use `presets/engineering.json`: 26 labels covering the provided `Status:`, `Type:`, and `Priority:` sets, plus engineering `Area:` labels for frontend, backend, API, database, CI/CD, documentation, security, observability, and performance.

Every label color is unique. Keep that invariant for custom edits.

**Done when** `presets/engineering.json` matches the user's requested label set.

## 3 — Preview

Run the non-destructive preview. Resolve `<skill_dir>` to this skill's directory:

```bash
uv run python <skill_dir>/scripts/reset_labels.py --preset <skill_dir>/presets/engineering.json [--repo <owner>/<repo>]
```

Report the repository, how many existing labels would be deleted, and how many labels would be created.

**Done when** the user has seen the delete/create counts for the exact repository and preset.

## 4 — Confirmation

Ask for this exact confirmation string, filled from the preview:

```text
reset labels in <owner>/<repo> with engineering
```

The exact string matters because the next step deletes repository labels. Any other wording stops the reset.

**Done when** the user provides the exact confirmation string.

## 5 — Apply

Run the reset with the same repo from the preview:

```bash
uv run python <skill_dir>/scripts/reset_labels.py \
  --preset <skill_dir>/presets/engineering.json \
  [--repo <owner>/<repo>] \
  --apply \
  --confirm 'reset labels in <owner>/<repo> with engineering'
```

The script uses `gh label list`, `gh label delete --yes`, and `gh label create`, then re-reads the labels and verifies exact names, colors, and descriptions.

**Done when** the script reports `Reset <owner>/<repo> to preset engineering`.

## 6 — Report

Report the applied preset and repository. If the reset fails midway, report the failing `gh` operation and re-run preview before any retry.

**Done when** the user has the final repository, preset, created label count, and any failure detail.
