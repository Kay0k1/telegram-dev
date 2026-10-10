from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_sources import check_sources, load_snapshot, render_status, write_outputs


class SourceMonitorTests(unittest.TestCase):
    urls = ["https://core.telegram.org/bots/api", "https://core.telegram.org/bots/webapps"]

    @staticmethod
    def fetch_document(url):
        return url, "Official document", "Document body with enough content to be valid. " + url, []

    def test_baseline_then_unchanged_preserves_change_time(self):
        first, first_report = check_sources(self.urls, {}, stamp="first", fetcher=self.fetch_document)
        self.assertEqual(first_report["counts"]["new"], 2)
        second, report = check_sources(self.urls, first, stamp="second", fetcher=self.fetch_document)
        self.assertEqual(report["counts"]["unchanged"], 2)
        self.assertTrue(report["healthy"])
        self.assertEqual(second["sources"][self.urls[0]]["changed_at"], "first")
        self.assertEqual(second["sources"][self.urls[0]]["checked_at"], "second")

    def test_changed_hash_updates_change_time_without_storing_content(self):
        previous, _ = check_sources(self.urls, {}, stamp="first", fetcher=self.fetch_document)

        def revised(url):
            result = self.fetch_document(url)
            return result[0], result[1], result[2] + " New documented feature.", []

        snapshot, report = check_sources(self.urls, previous, stamp="second", fetcher=revised)
        self.assertEqual(report["counts"]["changed"], 2)
        self.assertEqual(snapshot["sources"][self.urls[0]]["changed_at"], "second")
        self.assertNotIn("body", snapshot["sources"][self.urls[0]])
        self.assertNotEqual(report["sources"][0]["sha256"], report["sources"][0]["previous_sha256"])

    def test_failure_retains_previous_success_and_is_unhealthy(self):
        previous, _ = check_sources(self.urls[:1], {}, stamp="first", fetcher=self.fetch_document)

        def failing(_url):
            raise RuntimeError("source unavailable")

        snapshot, report = check_sources(self.urls, previous, stamp="second", attempts=1, fetcher=failing)
        self.assertFalse(report["healthy"])
        self.assertEqual(report["counts"]["failed"], 2)
        self.assertEqual(snapshot["sources"], previous["sources"])
        self.assertEqual(report["sources"][0]["last_successful_check"], "first")
        self.assertIsNone(report["sources"][1]["last_successful_check"])
        self.assertIn("RuntimeError: source unavailable", render_status(report))

    def test_snapshot_round_trip_and_escaped_status(self):
        snapshot, report = check_sources(self.urls, {}, fetcher=self.fetch_document, stamp="first")
        report["sources"][0]["title"] = "API | <test>\nnew line"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_outputs(output, snapshot, report)
            self.assertEqual(load_snapshot(output / "source-snapshot.json"), snapshot)
            self.assertTrue(json.loads((output / "source-report.json").read_text(encoding="utf-8"))["healthy"])
            self.assertIn("API \\| &lt;test&gt; new line", (output / "README.md").read_text(encoding="utf-8"))

    def test_invalid_or_empty_document_is_a_failure(self):
        for result in (("https://example.com", "Bad redirect", "long enough document text to inspect", []),
                       (self.urls[0], "Empty", "", [])):
            with self.subTest(result=result):
                snapshot, report = check_sources(self.urls[:1], {}, attempts=1, fetcher=lambda _url: result)
                self.assertFalse(report["healthy"])
                self.assertEqual(snapshot["sources"], {})

    def test_outside_url_and_corrupt_checkpoint_are_rejected(self):
        with self.assertRaises(ValueError):
            check_sources(["https://example.com"], {}, fetcher=self.fetch_document)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"schema_version": 1, "sources": {self.urls[0]: {"sha256": "bad"}}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_snapshot(path)


if __name__ == "__main__":
    unittest.main()
