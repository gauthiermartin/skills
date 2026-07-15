import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "delivery_metrics.py"
SPEC = importlib.util.spec_from_file_location("delivery_metrics", SCRIPT)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


class DeliveryMetricTests(unittest.TestCase):
    def test_nearest_rank_percentile(self) -> None:
        self.assertEqual(metrics.percentile_nearest_rank(list(range(1, 11)), 0.90), 9)
        self.assertIsNone(metrics.percentile_nearest_rank([], 0.90))

    def test_first_review_ignores_author_and_bots(self) -> None:
        reviews = [
            {"submitted_at": "2026-01-01T01:00:00Z", "user": {"login": "author", "type": "User"}},
            {"submitted_at": "2026-01-01T02:00:00Z", "user": {"login": "ci[bot]", "type": "Bot"}},
            {"submitted_at": "2026-01-01T03:00:00Z", "user": {"login": "reviewer", "type": "User"}},
            {"submitted_at": "2026-01-01T04:00:00Z", "user": {"login": "other", "type": "User"}},
        ]
        self.assertEqual(metrics.first_human_review(reviews, "author"), "2026-01-01T03:00:00Z")

    def test_canonical_reverts_extract_short_and_full_shas_with_timestamps(self) -> None:
        commits = [
            {"commit": {"committer": {"date": "2026-01-02T00:00:00Z"}, "message": "Revert \"broken\"\n\nThis reverts commit abcdef1."}},
            {"commit": {"committer": {"date": "2026-01-03T00:00:00Z"}, "message": "This reverts commit 0123456789abcdef0123456789abcdef01234567."}},
        ]
        self.assertEqual(
            metrics.reverted_merge_times(commits),
            {
                "abcdef1": [metrics.parse_time("2026-01-02T00:00:00Z")],
                "0123456789abcdef0123456789abcdef01234567": [metrics.parse_time("2026-01-03T00:00:00Z")],
            },
        )

    def test_age_boundary_is_strictly_more_than_seven_days(self) -> None:
        opened = metrics.parse_time("2026-01-01T00:00:00Z")
        self.assertFalse(metrics.parse_time("2026-01-08T00:00:00Z") - opened > metrics.timedelta(days=7))
        self.assertTrue(metrics.parse_time("2026-01-08T00:00:01Z") - opened > metrics.timedelta(days=7))

    def test_deleted_pr_author_does_not_abort_review_metrics(self) -> None:
        class GitHub:
            def review_data(self, repo: str, number: int):
                return []

        durations, unreviewed = metrics.review_metrics(
            GitHub(),
            "owner/repo",
            [{"number": 1, "createdAt": "2026-01-01T00:00:00Z", "author": None}],
        )
        self.assertEqual(durations, [])
        self.assertEqual(unreviewed, 1)

    def test_required_check_result_requires_terminal_results(self) -> None:
        class GitHub:
            def __init__(self, conclusion: str | None, state: str) -> None:
                self.conclusion = conclusion
                self.state = state

            def try_json(self, endpoint: str):
                if endpoint.endswith("check-runs?per_page=100"):
                    return {"check_runs": [{"name": "test", "conclusion": self.conclusion}]}, None
                return {"statuses": [{"context": "deploy", "state": self.state}]}, None

        required = {"test", "deploy"}
        self.assertTrue(metrics.failed_required_checks(GitHub("FAILURE", "success"), "owner/repo", "sha", required))
        self.assertFalse(metrics.failed_required_checks(GitHub("SUCCESS", "success"), "owner/repo", "sha", required))
        self.assertIsNone(metrics.failed_required_checks(GitHub(None, "pending"), "owner/repo", "sha", required))


if __name__ == "__main__":
    unittest.main()
