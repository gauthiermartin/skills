---
name: github-delivery-metrics
description: Collect a GitHub delivery-metrics report for a repository.
metadata:
  origin: gauthiermartin/skills
  origin-status: local
disable-model-invocation: true
---

`github-delivery-metrics` produces evidence about repository flow: merged PRs, review latency, WIP, PR size, required-check failures, detected reverts, and—when GitHub Deployments records production—deployment frequency and commit-to-production lead time. It reports unavailable data as unavailable; never convert missing incident or deployment evidence into zeroes.

## 1 — Target

Resolve the target repository:

```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
```

Use `--repo <owner>/<repo>` when the user names a repository outside the current checkout. The script needs an authenticated `gh` session with read access. If the API rejects a request, run `gh auth status` and report the missing repository permission rather than retrying with a different repository.

**Done when** the target is an `owner/repo` string GitHub can read.

## 2 — Window

Default to the previous 56 rolling UTC days. Use a shorter or longer window only when the user names it. The report groups merged PRs and successful deployments by UTC Monday-start week; it uses median and nearest-rank p90, not averages.

**Done when** the repository and window are explicit in the command.

## 3 — Collect

Resolve `<skill_dir>` to this skill directory, then run:

```bash
uv run python <skill_dir>/scripts/delivery_metrics.py \
  --repo <owner>/<repo> \
  --days 56 \
  --environment production \
  --json /tmp/<repo-name>-delivery-metrics.json
```

Use the actual GitHub production environment name when it differs from `production`. Skip deployment collection with `--environment ""` when the repository does not record deployments in GitHub.

The script collects:

- merged PR count, PR cycle-time median/p90, first-human-review median/p90, open WIP, PRs older than seven days, and PR-size median/p90;
- final required-check failure rate only when the default branch exposes classic required status checks;
- a lower-bound revert rate from canonical GitHub `This reverts commit <SHA>.` messages;
- successful GitHub Deployment frequency and a proven commit-to-production lead time when an environment is supplied.

**Done when** the command prints a report and writes valid JSON when `--json` was supplied.

## 4 — Interpret

Read flow and guardrails together:

- Faster cycle time with a rising revert or failed-check rate is unsafe flow.
- Rising aged PRs with flat merged volume indicates WIP or review congestion.
- More merged PRs with low deployment frequency indicates a release/deployment bottleneck.
- An unavailable DORA measure is a data-integration gap, not a favourable result.

GitHub alone cannot establish DORA change-failure rate or time to restore service. Incident, rollback, or observability evidence is required. A failed GitHub deployment status remains a deployment-failure proxy, not a DORA claim.

**Done when** the user receives the report, its denominators, and every unavailable metric's reason.
