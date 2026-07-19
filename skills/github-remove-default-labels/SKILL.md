---
name: github-remove-default-labels
description: Delete GitHub's nine seeded default labels from a repository using gh, after a preview and explicit confirmation.
metadata:
  origin: gauthiermartin/skills
  origin-status: local
disable-model-invocation: true
---

# github-remove-default-labels

Strip the nine labels GitHub seeds into every new repository: `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`. Deleting a label also removes it from any issue or PR carrying it, so nothing is deleted before the preview is confirmed.

## 1 — Repository

Resolve the target: an explicit `owner/repo` from the user, else infer it from `git remote -v` in the current directory.

**Done when** the target is an `owner/repo` string and `gh` can read its labels.

## 2 — Keep-list

The triage skills reuse `bug`, `enhancement`, and `wontfix` as canonical roles. If this repo will use the triage flow, keep those three; otherwise all nine are candidates. Ask which applies.

**Done when** the candidate list is settled.

## 3 — Preview

Read the repository's current labels:

```bash
gh label list --repo <owner>/<repo> --limit 1000 --json name --jq '.[].name'
```

Compare exact names against the candidate list and show the user every current label, marked as **delete** (a candidate that is present), **keep** (kept by step 2 or not a default), or note candidates **already absent**. The delete set is exactly the candidates present in the repo.

**Done when** the user has seen the full current label list and the computed delete set for the exact repository.

## 4 — Confirm

Ask the user to reply with exactly:

```text
remove default labels in <owner>/<repo>
```

The exact string matters because the next step deletes repository labels. Any other wording stops the run.

**Done when** the user provides the exact confirmation string.

## 5 — Delete

Delete only the computed delete set:

```bash
gh label delete "<name>" --repo <owner>/<repo> --yes
```

A "not found" error means the label vanished since the preview — reclassify it as already absent and continue. Any other `gh` error is a real failure: record it and report it, never as absent.

**Done when** every label in the delete set has been deleted, reclassified as absent, or recorded as a failure.

## 6 — Verify and report

Re-run the step 3 listing and confirm no name from the delete set remains. Report: repository, labels deleted, labels kept, labels already absent, and any failure with its `gh` error.

**Done when** the re-listing shows none of the delete set and every candidate is accounted for in exactly one bucket — deleted, kept, already absent, or failed.
