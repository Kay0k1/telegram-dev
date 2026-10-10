import concurrent.futures
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import telegram_knowledge as k


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = k.DB
        k.DB = Path(self.temp.name) / "refresh.sqlite3"
        self.url = "https://core.telegram.org/bots/api"
        self.env = patch.dict(os.environ, {"TELEGRAM_DOC_MAX_AGE_SECONDS": "21600"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        k.DB = self.old_db
        self.temp.cleanup()

    def seed(self, stale=False):
        with k.connect() as conn:
            k.save(conn, self.url, (self.url, "Bot API", "# sendVoice\noldFeature audio", []))
            if stale:
                stamp = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                conn.execute("UPDATE pages SET checked_at=?", (stamp,))

    def test_fresh_cache_avoids_network_and_stale_cache_refreshes(self):
        self.seed()
        with patch.object(k, "fetch") as fetch:
            doc = k.document(self.url)
            self.assertFalse(doc["freshness"]["stale"])
            fetch.assert_not_called()
        self.seed(stale=True)
        with patch.object(k, "fetch", return_value=(self.url, "Bot API", "# sendVoice\nnewFeature audio", [])) as fetch:
            doc = k.document(self.url)
            self.assertIn("newFeature", doc["body"])
            self.assertFalse(doc["freshness"]["stale"])
            fetch.assert_called_once_with(self.url)
        self.assertEqual(k.search("oldFeature")["results"], [])
        self.assertTrue(k.search("newFeature")["results"])

    def test_failed_refresh_preserves_content_and_backoff_is_visible(self):
        self.seed(stale=True)
        with patch.object(k, "fetch", side_effect=OSError("source temporarily offline")) as fetch:
            doc = k.document(self.url)
            again = k.document(self.url)
            self.assertIn("oldFeature", doc["body"])
            self.assertTrue(doc["freshness"]["stale"])
            self.assertIn("offline", doc["freshness"]["refresh_error"])
            self.assertEqual(doc["body"], again["body"])
            fetch.assert_called_once()
            k.document(self.url, refresh=True)
            self.assertEqual(fetch.call_count, 2)

    def test_search_refreshes_and_removes_obsolete_matches(self):
        self.seed(stale=True)
        with patch.object(k, "fetch", return_value=(self.url, "Bot API", "# sendVoice\nnewFeature audio", [])):
            self.assertEqual(k.search("oldFeature", refresh_results=True)["results"], [])
        self.assertFalse(k.search("newFeature")["results"][0]["freshness"]["stale"])

    def test_unchanged_source_refresh_migrates_old_api_family(self):
        url = "https://core.telegram.org/bots/telegram-login"
        body = "# Telegram Login\nOpenID Connect authorization discovery"
        with k.connect() as conn:
            k.save(conn, url, (url, "Login", body, []))
            conn.execute("UPDATE pages SET family='bot-api', checked_at='2020-01-01T00:00:00+00:00'")
            conn.execute("UPDATE chunks SET family='bot-api'")
            before = conn.execute("SELECT sha,changed_at FROM pages WHERE url=?", (url,)).fetchone()
        with patch.object(k, "fetch", return_value=(url, "Login", body, [])):
            doc = k.document(url)
        self.assertEqual(doc["sha"], before["sha"])
        self.assertEqual(doc["changed_at"], before["changed_at"])
        self.assertTrue(k.search("OpenID", "web-integrations")["results"])
        self.assertEqual(k.search("OpenID", "bot-api")["results"], [])

    def test_search_refreshes_newly_exposed_matches_after_source_changes(self):
        second = "https://core.telegram.org/api/entities"
        with k.connect() as conn:
            k.save(conn, self.url, (self.url, "Docs", "# exactSymbol\nexactSymbol old feature", []))
            k.save(conn, second, (second, "Docs", "# Other\nexactSymbol old feature", []))
            conn.execute("UPDATE pages SET checked_at='2020-01-01T00:00:00+00:00'")
        with patch.object(k, "fetch", side_effect=lambda url: (url, "Docs", "# Updated\nreplacementFeature", [])) as fetch:
            self.assertEqual(k.search("exactSymbol", limit=1, refresh_results=True)["results"], [])
            self.assertEqual({call.args[0] for call in fetch.call_args_list}, {self.url, second})

    def test_search_reordering_keeps_refresh_bounded_and_labels_remaining_cache(self):
        urls = [f"https://core.telegram.org/method/example{i}" for i in range(8)]
        with k.connect() as conn:
            for url in urls:
                k.save(conn, url, (url, "Docs", "# exactSymbol\nexactSymbol old feature", []))
            conn.execute("UPDATE pages SET checked_at='2020-01-01T00:00:00+00:00'")
        with patch.object(k, "fetch", side_effect=lambda url: (url, "Docs", "# Updated\nreplacementFeature", [])) as fetch:
            result = k.search("exactSymbol", limit=1, refresh_results=True)
            self.assertEqual(fetch.call_count, 6)
            self.assertEqual(len({call.args[0] for call in fetch.call_args_list}), 6)
            self.assertEqual(len(result["results"]), 1)
            self.assertTrue(result["results"][0]["freshness"]["stale"])

    def test_redirect_replaces_obsolete_index_and_reuses_alias(self):
        self.seed(stale=True)
        target = "https://core.telegram.org/bots/features"
        with patch.object(k, "fetch", return_value=(target, "Features", "# Messages\nnewFeature rich messages", [])) as fetch:
            self.assertEqual(k.document(self.url)["url"], target)
            self.assertEqual(k.document(self.url)["url"], target)
            fetch.assert_called_once()
        self.assertEqual(k.search("oldFeature")["results"], [])

    def test_concurrent_requests_refresh_one_page_once(self):
        self.seed(stale=True)
        with patch.object(k, "fetch", return_value=(self.url, "Bot API", "# sendVoice\nnewFeature audio", [])) as fetch:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                docs = list(pool.map(lambda _: k.document(self.url), range(16)))
            self.assertTrue(all("newFeature" in d["body"] for d in docs))
            fetch.assert_called_once()

    def test_background_budget_discovers_links_and_shared_schedule(self):
        child = "https://core.telegram.org/api/entities"
        with patch.object(k, "SEEDS", [self.url]), patch.object(k, "fetch", side_effect=lambda url: (url, "Docs", "# Entities\nmessage formatting entities", [child] if url == self.url else [])) as fetch:
            report = k.maintenance_tick(max_pages=2)
            self.assertEqual(report["processed"], 2)
            self.assertEqual(fetch.call_count, 2)
            self.assertEqual(k.coverage()["pages"], 2)
            self.assertTrue(k._claim_maintenance())
            self.assertFalse(k._claim_maintenance())

    def test_single_page_cycles_progress_across_seeds_links_and_failed_pages(self):
        second = "https://core.telegram.org/api/entities"
        child = "https://core.telegram.org/api/stories"
        failed = "https://core.telegram.org/method/recover"
        with k.connect() as conn:
            conn.execute("INSERT INTO frontier VALUES (?,'error','old failure')", (failed,))
        def fetch_doc(url):
            return url, "Docs", "# Updated\nCurrent Telegram documentation", [child] if url == self.url else []
        with patch.object(k, "SEEDS", [self.url, second]), patch.object(k, "fetch", side_effect=fetch_doc) as fetch:
            for _ in range(6):
                report = k.maintenance_tick(max_pages=1)
                self.assertLessEqual(report["processed"], 1)
                # A cycle interval at least as long as TTL makes earlier seeds
                # due again; it must still allow later sources to progress.
                with k.connect() as conn:
                    conn.execute("UPDATE pages SET checked_at='2020-01-01T00:00:00+00:00'")
            self.assertTrue({self.url, second, child, failed}.issubset({call.args[0] for call in fetch.call_args_list}))

    def test_background_retries_failed_links_even_when_many_pages_are_stale(self):
        self.seed(stale=True)
        missing = "https://core.telegram.org/api/stories"
        with k.connect() as conn:
            conn.execute("INSERT INTO frontier VALUES (?,'error','temporary failure')", (missing,))
            for i in range(10):
                url = f"https://core.telegram.org/method/example{i}"
                k.save(conn, url, (url, "Method", "# Method\nAn old documented API method", []))
            conn.execute("UPDATE pages SET checked_at='2020-01-01T00:00:00+00:00'")
        with patch.object(k, "SEEDS", []), patch.object(k, "fetch", side_effect=lambda url: (url, "Recovered", "# Updated\nDocumentation successfully fetched", [])) as fetch:
            k.maintenance_tick(max_pages=3)
            self.assertIn(missing, [call.args[0] for call in fetch.call_args_list])
            with k.connect() as conn:
                self.assertEqual(conn.execute("SELECT state FROM frontier WHERE url=?", (missing,)).fetchone()[0], "done")

    def test_shutdown_does_not_start_queued_network_requests(self):
        urls = [f"https://core.telegram.org/method/example{i}" for i in range(3)]
        stop, queued, release = threading.Event(), threading.Event(), threading.Event()
        started, reports = [], []
        class ObservedExecutor(concurrent.futures.ThreadPoolExecutor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.submitted = 0

            def submit(self, *args, **kwargs):
                future = super().submit(*args, **kwargs)
                self.submitted += 1
                if self.submitted == len(urls):
                    queued.set()
                return future

        def refresh(url, force=False):
            started.append(url)
            if not release.wait(timeout=5):
                raise AssertionError("Test did not release the active request")
            return {"error": None}

        with patch.object(k.concurrent.futures, "ThreadPoolExecutor", ObservedExecutor), patch.object(k, "refresh_page", side_effect=refresh):
            worker = threading.Thread(target=lambda: reports.extend(k._fetch_batch(urls, workers=1, stop=stop)))
            worker.start()
            try:
                self.assertTrue(queued.wait(timeout=2), "Requests were not queued")
                stop.set()
            finally:
                release.set()
                worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
        self.assertEqual(started, [urls[0]])
        self.assertEqual(reports, [{"url": urls[0], "error": None}])


if __name__ == "__main__":
    unittest.main()
