---
name: git-push
description: Push the current Git branch to its remote, setting upstream when missing.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
disable-model-invocation: true
---

A push **publishes** the named current branch through its resolved upstream. First identify the branch, then identify its upstream, then push through the narrowest command that matches that state.

## 1 — Branch

Resolve the current branch: `git branch --show-current`.

- If the result is empty, stop: detached HEAD has no branch upstream to set.
- Keep the working tree untouched: no branch switches, renames, commits, staging, stashing, pulls, rebases, merges, or fallback branches.

**Done when** HEAD is on a named branch and that branch name is the branch being published.

## 2 — Upstream

Resolve whether the branch already tracks a remote branch:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

- If the command succeeds, the branch has an upstream. Push with `git push`.
- If it fails, pick the remote for first publication:
  - Use `origin` when `git remote` lists it.
  - Use the only configured remote when exactly one remote exists.
  - Stop and ask which remote to use when multiple remotes exist and none is `origin`.
  - Stop when no remotes exist.

**Done when** the publish command is selected: `git push` for a tracked branch, or `git push -u <remote> HEAD` for an untracked branch.

## 3 — Publish

Run the selected command exactly once:

- Tracked branch: `git push`
- Missing upstream: `git push -u <remote> HEAD`

Treat push rejection as the result to report, not as permission to rewrite history. Leave history untouched unless the user asks for that follow-up.

**Done when** the push command exits successfully, or its rejection/error has been reported with the command that failed.

## 4 — Verify

After a successful push, verify the branch now has an upstream:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

Then report the published branch and upstream. If the push set the upstream, say so explicitly.

**Done when** the final response names the local branch, its upstream, and whether upstream was newly set or already present.
