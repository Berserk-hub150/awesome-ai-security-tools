"""Offline regression tests for snapshot refresh and explicit exclusions."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import update_github_metrics as updater


class SnapshotRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "sections.json"
        self.old = {"stars": 10, "updated": "2025-01-01", "snapshot": "2025-01-02"}
        self.fresh = {"stars": 20, "updated": "2026-10-12", "snapshot": "2026-10-13"}
        self.data = {"sections": [
            {"groups": [{"entries": [
                {"repo": "owner/active", "metrics": self.old, "note": "Keep this note."},
                {"repo": "owner/missing", "metrics": self.old},
                {"kind": "hf_model", "model": "owner/model", "license": "MIT"},
            ]}]},
            {"entries": [{"repo": "owner/related", "kind": "awesome_list"}]},
        ]}
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        self.original = self.path.read_bytes()

    def run_refresh(self, args=(), error=None):
        output, warnings = io.StringIO(), io.StringIO()

        def fetch(token, repos, snapshot):
            self.assertEqual(token, "test-token")
            if error:
                raise error
            return {repo: dict(self.fresh) for repo in repos}

        with patch.object(updater, "github_token", return_value="test-token") as auth, \
                patch.object(updater, "fetch_metrics", side_effect=fetch) as request, \
                patch("sys.argv", ["update_github_metrics.py", "--data", str(self.path), *args]), \
                redirect_stdout(output), redirect_stderr(warnings):
            code = updater.main()
        return code, output.getvalue(), warnings.getvalue(), auth, request

    def entries(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return list(updater.iter_entries(data))

    def test_default_refresh_includes_grouped_and_related_entries(self):
        code, output, warnings, _, request = self.run_refresh()
        self.assertEqual(code, 0)
        self.assertIn("Updated 3 GitHub metric snapshots", output)
        self.assertEqual(warnings, "")
        self.assertEqual(request.call_args.args[1],
                         ["owner/active", "owner/missing", "owner/related"])
        entries = self.entries()
        self.assertEqual(entries[0]["metrics"], self.fresh)
        self.assertEqual(entries[0]["note"], "Keep this note.")
        self.assertEqual(entries[2],
                         {"kind": "hf_model", "model": "owner/model", "license": "MIT"})

    def test_explicit_skip_preserves_old_snapshot_and_warns(self):
        code, output, warnings, _, request = self.run_refresh(
            ["--skip-repo", "owner/missing", "--skip-repo", "owner/missing"])
        self.assertEqual(code, 0)
        self.assertIn("explicitly skipped 1", output)
        self.assertIn("snapshot 2025-01-02", warnings)
        self.assertEqual(request.call_args.args[1], ["owner/active", "owner/related"])
        self.assertEqual(self.entries()[1]["metrics"], self.old)
        self.assertEqual(self.entries()[3]["metrics"], self.fresh)

    def test_skip_does_not_invent_metrics_for_entry_without_snapshot(self):
        code, _, warnings, _, _ = self.run_refresh(["--skip-repo", "owner/related"])
        self.assertEqual(code, 0)
        self.assertIn("snapshot unavailable", warnings)
        self.assertNotIn("metrics", self.entries()[3])

    def test_unknown_skip_fails_before_auth_or_write(self):
        code, _, warnings, auth, request = self.run_refresh(["--skip-repo", "owner/typo"])
        self.assertEqual(code, 2)
        self.assertIn("Cannot skip unlisted repositories", warnings)
        auth.assert_not_called()
        request.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_skipping_everything_fails_without_write(self):
        args = [arg for repo in ("active", "missing", "related")
                for arg in ("--skip-repo", f"owner/{repo}")]
        code, _, warnings, auth, request = self.run_refresh(args)
        self.assertEqual(code, 2)
        self.assertIn("No repositories selected", warnings)
        auth.assert_not_called()
        request.assert_not_called()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_unskipped_api_error_still_fails_without_write(self):
        code, _, warnings, _, _ = self.run_refresh(
            ["--skip-repo", "owner/missing"], updater.MetricError("API unavailable"))
        self.assertEqual(code, 2)
        self.assertIn("API unavailable", warnings)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_fetch_uses_default_branch_commit_before_push_date(self):
        response = {"r0": {"stargazerCount": 7, "pushedAt": "2026-10-13T00:00:00Z",
                           "defaultBranchRef": {"target": {"committedDate": "2025-05-02T00:00:00Z"}}}}
        with patch.object(updater, "graphql", return_value=response):
            metrics = updater.fetch_metrics("test-token", ["owner/repo"], "2026-10-13")
        self.assertEqual(metrics["owner/repo"]["updated"], "2025-05-02")

    def test_fetch_falls_back_to_push_date_without_default_branch(self):
        response = {"r0": {"stargazerCount": 0, "pushedAt": "2026-10-13T00:00:00Z",
                           "defaultBranchRef": None}}
        with patch.object(updater, "graphql", return_value=response):
            metrics = updater.fetch_metrics("test-token", ["owner/repo"], "2026-10-13")
        self.assertEqual(metrics["owner/repo"],
                         {"stars": 0, "updated": "2026-10-13", "snapshot": "2026-10-13"})

    def test_fetch_does_not_replace_missing_repo_with_zero_metrics(self):
        with patch.object(updater, "graphql", return_value={"r0": None}):
            with self.assertRaises(updater.MetricError):
                updater.fetch_metrics("test-token", ["owner/missing"], "2026-10-13")


if __name__ == "__main__":
    unittest.main()
