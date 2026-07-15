#!/usr/bin/env python3
"""Collect repository delivery metrics using the GitHub API through gh."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

FAILURE_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "startup_failure",
    "stale",
    "timed_out",
}
REVERT_COMMIT = re.compile(r"This reverts commit ([0-9a-f]{7,40})\.", re.IGNORECASE)


class GitHubError(RuntimeError):
    pass


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def iso_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def percentile_nearest_rank(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def minutes_between(start: str, end: str) -> float:
    return (parse_time(end) - parse_time(start)).total_seconds() / 60


def week_start(value: datetime) -> str:
    return (value - timedelta(days=value.weekday())).date().isoformat()


def is_human(author: dict[str, Any] | None, pr_author: str | None) -> bool:
    if not author:
        return False
    login = author.get("login")
    return bool(
        login
        and login != pr_author
        and author.get("type") != "Bot"
        and not login.endswith("[bot]")
    )


def first_human_review(review_data: list[dict[str, Any]], pr_author: str | None) -> str | None:
    submitted = [
        review["submitted_at"]
        for review in review_data
        if review.get("submitted_at") and is_human(review.get("user"), pr_author)
    ]
    return min(submitted, key=parse_time) if submitted else None


def reverted_merge_times(commits: list[dict[str, Any]]) -> dict[str, list[datetime]]:
    result: dict[str, list[datetime]] = {}
    for item in commits:
        commit = item.get("commit") or {}
        reverted_at = (commit.get("committer") or {}).get("date")
        if not reverted_at:
            continue
        for sha in REVERT_COMMIT.findall(commit.get("message", "")):
            result.setdefault(sha.lower(), []).append(parse_time(reverted_at))
    return result


def format_minutes(value: float | None) -> str:
    if value is None:
        return "n/a"
    total = round(value)
    days, remainder = divmod(total, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def markdown_table(rows: list[tuple[str, str, str]]) -> list[str]:
    return [
        "| Metric | Value | Notes |",
        "| --- | ---: | --- |",
        *[f"| {metric} | {value} | {notes} |" for metric, value, notes in rows],
    ]


class GitHub:
    def __init__(self) -> None:
        self._compare_cache: dict[tuple[str, str], bool] = {}

    def run(self, args: list[str], payload: dict[str, Any] | None = None) -> str:
        process = subprocess.run(
            ["gh", *args],
            input=json.dumps(payload) if payload is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if process.returncode:
            raise GitHubError(process.stderr.strip() or "gh command failed")
        return process.stdout

    def json(self, endpoint: str) -> Any:
        return json.loads(self.run(["api", endpoint]))

    def try_json(self, endpoint: str) -> tuple[Any | None, str | None]:
        try:
            return self.json(endpoint), None
        except GitHubError as error:
            return None, str(error)

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        return json.loads(self.run(["api", "graphql", "--input", "-"], {"query": query, "variables": variables}))

    def repo_name(self, repo: str | None) -> str:
        if repo:
            return repo
        return self.run(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).strip()

    def paged_rest(self, endpoint: str) -> list[dict[str, Any]]:
        separator = "&" if "?" in endpoint else "?"
        result: list[dict[str, Any]] = []
        for page in range(1, 10_001):
            data = self.json(f"{endpoint}{separator}per_page=100&page={page}")
            if not isinstance(data, list):
                raise GitHubError(f"Expected list from {endpoint}")
            result.extend(data)
            if len(data) < 100:
                return result
        raise GitHubError(f"Pagination limit exceeded for {endpoint}")

    def review_data(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.paged_rest(f"repos/{repo}/pulls/{number}/reviews")

    def commit_data(self, repo: str, number: int) -> list[dict[str, Any]]:
        return self.paged_rest(f"repos/{repo}/pulls/{number}/commits")

    def contains_commit(self, repo: str, base: str, head: str) -> bool:
        key = (base, head)
        if key not in self._compare_cache:
            data, _ = self.try_json(f"repos/{repo}/compare/{base}...{head}")
            self._compare_cache[key] = bool(data and data.get("status") in {"ahead", "identical"})
        return self._compare_cache[key]


MERGED_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: ISSUE, first: 100, after: $cursor) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number url createdAt mergedAt additions deletions headRefOid
        author { login }
        mergeCommit { oid }
      }
    }
  }
}
"""

OPEN_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    pullRequests(first: 100, after: $cursor, states: OPEN) {
      pageInfo { hasNextPage endCursor }
      nodes { number url createdAt author { login } }
    }
  }
}
"""

DEPLOYMENTS_QUERY = """
query($owner: String!, $name: String!, $environment: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    deployments(
      first: 100
      after: $cursor
      environments: [$environment]
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt
        commit { oid }
        statuses(first: 100) {
          totalCount
          nodes { state createdAt }
        }
      }
    }
  }
}
"""


def split_repo(repo: str) -> tuple[str, str]:
    owner, separator, name = repo.partition("/")
    if not owner or not separator or not name:
        raise GitHubError(f"Invalid repository {repo!r}; use owner/repo")
    return owner, name


def merged_prs(github: GitHub, repo: str, since: datetime) -> tuple[list[dict[str, Any]], bool]:
    query = f"repo:{repo} is:pr is:merged merged:>={since.date().isoformat()}"
    cursor: str | None = None
    prs: list[dict[str, Any]] = []
    issue_count = 0
    while True:
        data = github.graphql(MERGED_QUERY, {"query": query, "cursor": cursor})["data"]["search"]
        issue_count = data["issueCount"]
        prs.extend(node for node in data["nodes"] if node and node.get("mergedAt"))
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
        if len(prs) >= 1000:
            break
    window_prs = [pr for pr in prs if parse_time(pr["mergedAt"]) >= since]
    return window_prs, issue_count > len(prs)


def open_prs(github: GitHub, repo: str) -> tuple[list[dict[str, Any]], str]:
    owner, name = split_repo(repo)
    cursor: str | None = None
    prs: list[dict[str, Any]] = []
    branch: str | None = None
    while True:
        repository = github.graphql(OPEN_QUERY, {"owner": owner, "name": name, "cursor": cursor})["data"]["repository"]
        if branch is None:
            default_branch = repository.get("defaultBranchRef")
            if not default_branch:
                raise GitHubError(f"{repo} has no default branch")
            branch = default_branch["name"]
        connection = repository["pullRequests"]
        prs.extend(connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]
    return prs, branch or ""


def review_metrics(github: GitHub, repo: str, prs: list[dict[str, Any]]) -> tuple[list[float], int]:
    durations: list[float] = []
    unreviewed = 0
    for pr in prs:
        first = first_human_review(github.review_data(repo, pr["number"]), (pr.get("author") or {}).get("login"))
        if first is None:
            unreviewed += 1
        else:
            durations.append(minutes_between(pr["createdAt"], first))
    return durations, unreviewed


def required_checks(github: GitHub, repo: str, branch: str) -> tuple[set[str] | None, str | None]:
    data, error = github.try_json(f"repos/{repo}/branches/{branch}/protection/required_status_checks")
    if data is None:
        return None, error
    contexts = set(data.get("contexts", []))
    contexts.update(check["context"] for check in data.get("checks", []) if check.get("context"))
    if not contexts:
        return None, "default branch has no required status checks"
    return contexts, None


def failed_required_checks(github: GitHub, repo: str, sha: str, required: set[str]) -> bool | None:
    runs, run_error = github.try_json(f"repos/{repo}/commits/{sha}/check-runs?per_page=100")
    statuses, status_error = github.try_json(f"repos/{repo}/commits/{sha}/status")
    if runs is None or statuses is None:
        return None
    run_conclusions = {
        run["name"]: run["conclusion"].lower()
        for run in runs.get("check_runs", [])
        if run.get("name") in required and run.get("conclusion") is not None
    }
    status_states = {
        status["context"]: status["state"]
        for status in statuses.get("statuses", [])
        if status.get("context") in required and status.get("state") in {"success", "error", "failure"}
    }
    if not required.issubset(set(run_conclusions).union(status_states)):
        return None
    return any(
        conclusion in FAILURE_CONCLUSIONS for conclusion in run_conclusions.values()
    ) or any(state in {"error", "failure"} for state in status_states.values())


def first_commit_time(github: GitHub, repo: str, number: int) -> str | None:
    timestamps = [
        ((item.get("commit") or {}).get("author") or {}).get("date")
        for item in github.commit_data(repo, number)
    ]
    known = [timestamp for timestamp in timestamps if timestamp]
    return min(known, key=parse_time) if known else None


def deployment_metrics(
    github: GitHub,
    repo: str,
    environment: str,
    since: datetime,
    merged: list[dict[str, Any]],
) -> dict[str, Any]:
    owner, name = split_repo(repo)
    cursor: str | None = None
    deployments: list[dict[str, Any]] = []
    status_history_complete = True
    while True:
        repository = github.graphql(
            DEPLOYMENTS_QUERY,
            {"owner": owner, "name": name, "environment": environment, "cursor": cursor},
        )["data"]["repository"]
        connection = repository["deployments"]
        recent = [node for node in connection["nodes"] if parse_time(node["createdAt"]) >= since]
        deployments.extend(recent)
        status_history_complete &= all(
            node["statuses"]["totalCount"] == len(node["statuses"]["nodes"])
            for node in recent
        )
        if len(recent) < len(connection["nodes"]) or not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]

    successful: list[dict[str, Any]] = []
    failed = 0
    for deployment in deployments:
        statuses = deployment["statuses"]["nodes"]
        successes = [status for status in statuses if status["state"] == "SUCCESS"]
        if successes:
            success = min(successes, key=lambda status: parse_time(status["createdAt"]))
            successful.append({
                "sha": (deployment.get("commit") or {}).get("oid"),
                "at": success["createdAt"],
            })
        elif any(status["state"] in {"ERROR", "FAILURE"} for status in statuses):
            failed += 1

    successful.sort(key=lambda deployment: parse_time(deployment["at"]))
    weekly = Counter(week_start(parse_time(item["at"])) for item in successful)
    lead_times: list[float] = []
    comparison_limit = 1_000
    comparisons = 0
    incomplete = not status_history_complete
    for pr in merged:
        merge_sha = (pr.get("mergeCommit") or {}).get("oid")
        if not merge_sha:
            continue
        candidates = [
            item for item in successful
            if item["sha"] and parse_time(item["at"]) >= parse_time(pr["mergedAt"])
        ]
        deployment: dict[str, Any] | None = None
        for candidate in candidates:
            if candidate["sha"] == merge_sha:
                deployment = candidate
                break
            if comparisons >= comparison_limit:
                incomplete = True
                break
            comparisons += 1
            if github.contains_commit(repo, merge_sha, candidate["sha"]):
                deployment = candidate
                break
        if incomplete:
            break
        if deployment:
            start = first_commit_time(github, repo, pr["number"])
            if start:
                lead_times.append(minutes_between(start, deployment["at"]))

    return {
        "available": True,
        "environment": environment,
        "successful_deployments": len(successful),
        "weekly_successful_deployments": dict(sorted(weekly.items())),
        "failed_deployment_proxy": failed,
        "lead_time_minutes": lead_times,
        "lead_time_complete": not incomplete,
        "status_history_complete": status_history_complete,
        "comparisons": comparisons,
        "limitation": "Deployment history is ordered by creation time; a deployment created before the window but completed inside it is excluded.",
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now(UTC)
    since = now - timedelta(days=args.days)
    github = GitHub()
    repo = github.repo_name(args.repo)
    merged, merged_truncated = merged_prs(github, repo, since)
    open_items, default_branch = open_prs(github, repo)

    cycle_times = [minutes_between(pr["createdAt"], pr["mergedAt"]) for pr in merged]
    sizes = [float(pr["additions"] + pr["deletions"]) for pr in merged]
    review_times, unreviewed = review_metrics(github, repo, merged)
    old_open = sorted(
        [
            {
                "number": pr["number"],
                "url": pr["url"],
                "age_days": round((now - parse_time(pr["createdAt"])).total_seconds() / 86_400, 1),
            }
            for pr in open_items
            if now - parse_time(pr["createdAt"]) > timedelta(days=7)
        ],
        key=lambda pr: pr["age_days"],
        reverse=True,
    )

    required, required_reason = required_checks(github, repo, default_branch)
    check_data: dict[str, Any]
    if required is None:
        check_data = {"available": False, "reason": required_reason}
    else:
        results = [
            failed_required_checks(github, repo, pr["headRefOid"], required)
            for pr in merged
            if pr.get("headRefOid")
        ]
        evaluated = [result for result in results if result is not None]
        check_data = {
            "available": bool(evaluated),
            "required_checks": sorted(required),
            "evaluated_prs": len(evaluated),
            "unresolved_prs": len(results) - len(evaluated),
            "failed_prs": sum(result is True for result in evaluated),
            "rate": sum(result is True for result in evaluated) / len(evaluated) if evaluated else None,
            "reason": None if evaluated else "No required checks were resolved on merged PR head SHAs",
        }

    revert_times = reverted_merge_times(
        github.paged_rest(
            f"repos/{repo}/commits?sha={default_branch}&since={iso_time(since)}&until={iso_time(now)}"
        )
    )
    revert_eligible = [
        pr for pr in merged
        if parse_time(pr["mergedAt"]) + timedelta(days=30) <= now
    ]
    reverted = [
        pr for pr in revert_eligible
        if any(
            parse_time(pr["mergedAt"]) <= reverted_at <= parse_time(pr["mergedAt"]) + timedelta(days=30)
            for reverted_sha, reverted_at_values in revert_times.items()
            if (pr.get("mergeCommit") or {}).get("oid", "").lower().startswith(reverted_sha)
            for reverted_at in reverted_at_values
        )
    ]

    deployments = (
        deployment_metrics(github, repo, args.environment, since, merged)
        if args.environment else {"available": False, "reason": "No deployment environment requested"}
    )
    return {
        "repository": repo,
        "generated_at": iso_time(now),
        "window": {"since": iso_time(since), "until": iso_time(now), "days": args.days},
        "flow": {
            "merged_prs": len(merged),
            "merged_prs_truncated": merged_truncated,
            "weekly_merged_prs": dict(sorted(Counter(week_start(parse_time(pr["mergedAt"])) for pr in merged).items())),
            "cycle_time_minutes": cycle_times,
            "pr_size_lines": sizes,
            "first_review_minutes": review_times,
            "unreviewed_prs": unreviewed,
            "open_prs": len(open_items),
            "aged_open_prs": old_open,
        },
        "checks": check_data,
        "reverts": {
            "eligible_prs": len(revert_eligible),
            "censored_prs": len(merged) - len(revert_eligible),
            "detected_reverted_prs": len(reverted),
            "rate": len(reverted) / len(revert_eligible) if revert_eligible else None,
            "window_days": 30,
            "limitation": "Only canonical GitHub revert messages referencing a PR merge commit are counted.",
        },
        "deployments": deployments,
    }


def render(report: dict[str, Any]) -> str:
    flow = report["flow"]
    checks = report["checks"]
    deployments = report["deployments"]
    cycle = flow["cycle_time_minutes"]
    review = flow["first_review_minutes"]
    size = flow["pr_size_lines"]
    lines = [
        f"# Delivery metrics — {report['repository']}",
        "",
        f"Window: {report['window']['since']} to {report['window']['until']} (UTC)",
        "",
        "## GitHub flow",
        *markdown_table([
            ("Merged PRs", str(flow["merged_prs"]), "Merged in the reporting window."),
            ("PR cycle time", f"median {format_minutes(median(cycle))}; p90 {format_minutes(percentile_nearest_rank(cycle, 0.90))}", "Opened to merged."),
            ("Time to first human review", f"median {format_minutes(median(review))}; p90 {format_minutes(percentile_nearest_rank(review, 0.90))}", f"{flow['unreviewed_prs']} merged PRs had no human review."),
            ("Open PR WIP", str(flow["open_prs"]), "Snapshot at collection time."),
            ("PR size", f"median {median(size) or 0:.0f} lines; p90 {percentile_nearest_rank(size, 0.90) or 0:.0f} lines", "Additions plus deletions."),
        ]),
        "",
        "## Aged open PRs (>7 days)",
    ]
    if flow["aged_open_prs"]:
        lines.extend(f"- #{pr['number']} — {pr['age_days']} days — {pr['url']}" for pr in flow["aged_open_prs"])
    else:
        lines.append("None.")

    lines.extend(["", "## Guardrails"])
    if checks["available"]:
        lines.extend(markdown_table([
            ("Final required-check failure rate", f"{checks['rate']:.1%}", f"{checks['failed_prs']} of {checks['evaluated_prs']} resolved PR heads."),
            ("Detected merge-commit revert rate", f"{report['reverts']['rate']:.1%}" if report["reverts"]["rate"] is not None else "n/a", f"{report['reverts']['detected_reverted_prs']} of {report['reverts']['eligible_prs']} mature PRs; {report['reverts']['censored_prs']} censored; lower bound."),
        ]))
    else:
        lines.extend(markdown_table([
            ("Final required-check failure rate", "unavailable", checks.get("reason") or "GitHub did not expose required checks."),
            ("Detected merge-commit revert rate", f"{report['reverts']['rate']:.1%}" if report["reverts"]["rate"] is not None else "n/a", f"{report['reverts']['detected_reverted_prs']} of {report['reverts']['eligible_prs']} mature PRs; {report['reverts']['censored_prs']} censored; lower bound."),
        ]))

    lines.extend(["", "## DORA-style deployment evidence"])
    if deployments["available"]:
        lead_times = deployments["lead_time_minutes"]
        lead = (
            f"median {format_minutes(median(lead_times))}; p90 {format_minutes(percentile_nearest_rank(lead_times, 0.90))}"
            if deployments["lead_time_complete"] else "unavailable: incomplete deployment history or comparison budget exhausted"
        )
        lines.extend(markdown_table([
            ("Successful production deployments", str(deployments["successful_deployments"]), f"Environment: {deployments['environment']}."),
            ("Commit-to-production lead time", lead, "First PR commit to the first proven deployment containing its merge commit."),
            ("Failed deployment-status proxy", str(deployments["failed_deployment_proxy"]), "Not DORA change failure rate."),
            ("Change failure rate", "unavailable", "Requires incident, rollback, or customer-impact attribution."),
            ("Time to restore service", "unavailable", "Requires incident or observability data."),
        ]))
        lines.append(f"> Data quality: {deployments['limitation']}")
        if not deployments["status_history_complete"]:
            lines.append("> Data quality: At least one deployment has more than 100 statuses; deployment counts and failure proxy are incomplete.")
    else:
        lines.append(f"Unavailable: {deployments['reason']}")

    if flow["merged_prs_truncated"]:
        lines.extend(["", "> Data quality: GitHub search returned more than 1,000 merged PRs; the merged-PR cohort is incomplete."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect GitHub delivery metrics through gh.")
    parser.add_argument("--repo", help="owner/repo; defaults to the current gh repository")
    parser.add_argument("--days", type=int, default=56, help="Rolling UTC reporting window (default: 56)")
    parser.add_argument("--environment", default="production", help="GitHub deployment environment; pass an empty string to skip deployment data")
    parser.add_argument("--json", type=Path, help="Write the full machine-readable report to this path")
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")
    try:
        report = collect(args)
    except GitHubError as error:
        raise SystemExit(f"GitHub API error: {error}") from error
    print(render(report), end="")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
