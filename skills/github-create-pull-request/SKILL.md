---
name: github-create-pull-request
description: Create a GitHub pull request from the current branch.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
disable-model-invocation: true
---

A GitHub pull request is created in five moves — branch, base, template, publish, create. Resolve the two endpoints, build the body from the repo's template, make sure the head is on the remote, then create the PR through `gh`. Requires `gh` authenticated (`gh auth status`).

## 1 — Branch (head)

Resolve the head branch: `git branch --show-current`.

- Empty → detached HEAD has no branch to open a PR from; stop.
- On the default branch → there is nothing to merge; stop and report. Resolve the default with `git symbolic-ref --short refs/remotes/origin/HEAD` (fall back to `main`) and compare against the head after stripping the `origin/` prefix (`origin/main` → `main`). The head must be a feature branch (the `git-commit` skill creates one).
- Already has an open PR (`gh pr list --head <branch> --state open --json number,url`) → report its URL and stop; never open a second. This needs only the branch name, so it short-circuits before any body work. (Updating an already-open PR is the `git-push` skill's job.)

Leave the working tree as-is: no switches, commits, staging, or stashing here.

**Done when** HEAD is on a named non-default branch with no PR already open — the PR's head.

## 2 — Base

The branch the PR merges into. Default to the repo's default branch:

```bash
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
```

Use a base the user names instead when they give one. The base must differ from the head — GitHub rejects a PR whose head and base are the same branch.

**Done when** a base branch is chosen and differs from the head.

## 3 — Template

A repo often ships a PR template the body should follow. Find it in the working tree; when it exists in several spots the precedence is `.github/` → root → `docs/`.

**Single default template** — filename `pull_request_template` (case-insensitive), extension `.md` or `.txt`, in one of three locations:

| Location | Path |
|---|---|
| `.github/` | `.github/pull_request_template.md` |
| Root | `pull_request_template.md` |
| `docs/` | `docs/pull_request_template.md` |

**Multiple templates** — a `PULL_REQUEST_TEMPLATE/` directory (name uppercase) in any of those same three locations, one file per template (`.github/PULL_REQUEST_TEMPLATE/bugfix.md`, `.../feature.md`, …). Pick the file whose name fits the change — a `fix/` branch → `bugfix.md`; ask which to use when the match is ambiguous. (The web UI selects these via `?template=<name>.md`; here you read the chosen file directly.)

Read the chosen file and **fill it** — answer its prompts, check the boxes that apply, delete sections that don't. A template submitted with its instructional placeholders still in place is worse than no template. Derive the content from the branch's commits (`git log <base>..HEAD`) and `git diff <base>...HEAD`, not guesswork.

If no template exists, compose the body: a short paragraph on *what* changed and *why*, then a bullet list of the notable changes.

**Done when** a filled body exists — the repo's template with real content, or a composed body when the repo has none.

## 4 — Publish

`gh pr create` needs the head branch and all its commits on the remote. Check the upstream:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

- No upstream → publish with `git push -u <remote> HEAD` (`origin`, or the sole remote; ask when several exist and none is `origin`).
- Upstream exists but the branch is ahead → `git push`, so the PR includes every commit.

This mirrors the `git-push` skill; leave the rest of the tree untouched — no rebases, merges, or switches.

**Done when** the head branch and all its commits exist on the remote.

## 5 — Create

Title: Conventional-Commit style, `<type>(<scope>): <subject>`, matching the branch's commits. A single-commit branch reuses that commit's subject; a multi-commit branch synthesizes from the dominant change using the same type table the `git-commit` skill uses.

Write the body to a temp file and create with `--body-file` — multi-line bodies with backticks and lists don't survive shell-escaping through `--body`:

```bash
gh pr create --base <base> --head <branch> \
  --title "<title>" --body-file <tmpfile> [--draft]
```

- `--draft` when the user asks for a draft or the branch is work-in-progress.
- In a fork, `gh` targets the parent repo by default; pass `--repo <owner>/<repo>` to redirect.

**Done when** `gh pr create` returns the PR URL — report it with `base ← head`. A rejection is reported with the failing command, not worked around.
