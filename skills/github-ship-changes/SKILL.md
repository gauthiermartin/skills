---
name: github-ship-changes
description: Ship the current work to a GitHub pull request — runs git-commit, git-push, github-create-pull-request in sequence.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
disable-model-invocation: true
---

`github-ship-changes` **ships** the working tree all the way to a GitHub pull request in three moves — commit, push, PR — each delegated whole to the skill that owns it. Run them in order; each move's gate must hold before the next begins. Any move that stops itself (nothing to ship, detached HEAD, a remote or template choice to make, a push rejection) stops the ship: report where it halted and why, and leave the tree as the stopped skill left it.

## 1 — Commit

Follow `../git-commit/SKILL.md` to completion: it branches, updates the changelog, and lands every logical change as its own commit.

**Gate:** HEAD is on a feature branch carrying commits the base branch lacks. If `git-commit` committed nothing and the branch is level with base, there is nothing to ship — stop and report.

## 2 — Push

Follow `../git-push/SKILL.md` to completion: it publishes the branch through its upstream, setting one on first publication.

**Gate:** the branch and all its commits are on the remote.

## 3 — Pull request

Follow `../github-create-pull-request/SKILL.md` to completion: it resolves the base, fills the repo's template, and creates the PR.

**Gate:** a PR for the branch is open. Report it as the ship's result — the URL `github-create-pull-request` created, or the existing one it found.
