---
name: anvil-git-commit
description: Commit pending changes — semantic branch, changelog entry, atomic staging, Conventional Commit message.
disable-model-invocation: true
---

A commit **lands** in four moves — branch, changelog, index, message. A worktree holding several logical changes lands as several commits: moves 3–4 repeat once per change. Never skip a move because the change looks small.

## 1 — Branch

Resolve where you are: `git branch --show-current`; the default branch from `git symbolic-ref --short refs/remotes/origin/HEAD` (fall back to `main`).

- On the default branch, or detached HEAD: derive `<type>/<kebab-description>` from the dominant change (type from the table below, description ≤ 4 kebab-case words) and `git switch -c` it. A commit never lands on the default branch.
- On a branch that fails `^(feat|fix|chore|docs|refactor|test|ci|build|perf|style|revert)/[a-z0-9._/-]+$` — the same pattern the `semantic-branch-names` ruleset enforces server-side: no upstream → `git branch -m` to a conforming name; already pushed → keep it, warn that the ruleset may reject its pushes, and continue.

**Done when** HEAD is on a non-default branch matching the pattern — or on a pushed non-conforming branch you have warned about.

## 2 — Changelog

Find the changelog covering the changed files: the nearest `CHANGELOG*` walking up from each changed file, ignoring vendored directories (`node_modules/`, `vendor/`).

- **Manually maintained** — no release tooling generates it (no `.releaserc*`, `release.config.*`, `.changeset/`, `release-please-config.json`, `.release-please-manifest.json`, or `release` key in `package.json`, checked from the changelog's directory upward): add an entry in the file's existing format; it stages with the logical change it describes.
- **Tool-generated**: never hand-edit it — that conflicts at release time. Tell the user it was left alone; its entry will be derived from the commit message, which raises the stakes on step 4.
- **Absent**: say so and move on.

**Done when** the changelog is modified to reflect the change, or you have told the user it is generated or absent.

## 3 — Split & stage

`git status --porcelain` and `git diff` (staged and unstaged) first, always. Partition everything pending into **logical changes**: the files and hunks serving one purpose take one type/scope and land as one commit — nothing lands mixed. Changes serving no discernible purpose (scratch files, local config) stay unstaged and get reported.

Stage one logical change at a time, by explicit path — never `git add -A` or `git add .`. If the worktree holds only changes unrelated to what the user wants committed, stop and report instead.

**Done when** `git diff --cached --stat` lists exactly one logical change's files, plus its changelog entry from step 2.

## 4 — Message

`<type>(<scope>): <subject>` — type is usually the branch's type; scope is the one component touched (in a plugin monorepo, the plugin directory name), omitted when the change spans components.

Subject: imperative mood, ≤ 72 characters, stating *what changed* — precise enough that `git log --oneline` alone tells a reader whether this commit could explain their bug. Body: states *why* (motivation, trade-off, constraint), wrapped at 72; required whenever the why is not obvious from the diff, omitted otherwise.

```
fix(youtube-skills): resolve vtt_to_text.py via CLAUDE_PLUGIN_ROOT

Relative paths break when the skill runs outside the plugin dir;
the env var is the only stable anchor.
```

A breaking change takes `!` before the `:` and a `BREAKING CHANGE:` footer. That footer is what release tooling (semantic-release, release-please) majors on — never add it decoratively.

**Done when** the commit exists (`git log -1`) — then return to step 3 while logical changes remain. The run ends when `git status` shows only files deliberately left behind.

## Types

Pick by the change's *effect*, not its size:

| type | effect | release |
|---|---|---|
| feat | new capability a user can see | minor |
| fix | wrong behavior corrected | patch |
| perf | same behavior, measurably cheaper | patch |
| refactor | code reshaped, behavior identical | none |
| docs, test, ci, build, style, chore | literal | none |
| revert | undoes a shipped commit | mirrors it |

Recurring disambiguations: fixing your own unshipped work is part of the original type, not `fix`; a dependency bump is `chore` unless it changes user-visible behavior (`fix`/`feat`); `style` is formatting only — a rename is `refactor`.
