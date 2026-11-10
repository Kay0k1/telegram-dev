import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import telegram_knowledge as k


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = k.DB
        k.DB = Path(self.temp.name) / "test.sqlite3"

    def tearDown(self):
        k.DB = self.old_db
        self.temp.cleanup()

    def test_resumed_sync_completes_cached_pages_and_respects_failure_backoff(self):
        url = "https://core.telegram.org/bots/api"
        unavailable = "https://core.telegram.org/api/entities"
        with k.connect() as conn:
            k.save(conn, url, (url, "Bot API", "# sendVoice\nDocumented voice message method", []))
            conn.execute("INSERT INTO frontier VALUES (?,'pending',NULL)", (unavailable,))
            conn.execute("INSERT INTO attempts VALUES (?,?,?)", (unavailable, k.now(), "source temporarily offline"))
            conn.execute("UPDATE frontier SET state='pending'")
        with patch.object(k, "SEEDS", [url, unavailable]), patch.object(k, "fetch") as fetch:
            status = k.sync(max_pages=2, workers=1)
        fetch.assert_not_called()
        self.assertEqual(status["frontier"].get("pending", 0), 0)
        self.assertEqual(status["frontier"]["done"], 1)
        self.assertEqual(status["frontier"]["error"], 1)

    def test_changes_replace_search_but_preserve_history(self):
        url = "https://core.telegram.org/bots/api"
        with k.connect() as conn:
            k.save(conn, url, (url, "Bot API", "# sendVideoNote\noldMarker video note", []))
            k.save(conn, url, (url, "Bot API", "# sendVideoNote\nnewMarker video note", []))
            self.assertEqual(conn.execute("SELECT count(*) FROM revisions").fetchone()[0], 2)
        self.assertEqual(k.search("oldMarker")["results"], [])
        self.assertEqual(k.search("newMarker")["results"][0]["url"], url)

    def test_filter_and_paginate(self):
        bot = "https://core.telegram.org/bots/api"
        client = "https://core.telegram.org/api/entities"
        body = "# entities\n" + "😀 formatted text " * 1000
        with k.connect() as conn:
            for url in (bot, client):
                k.save(conn, url, (url, "Entities", body, []))
        results = k.search("entities", area="bot-api")["results"]
        self.assertTrue(results)
        self.assertTrue(all(r["url"] == bot for r in results))
        self.assertGreaterEqual(results[0]['document_offset'], 0)
        collected, offset = "", 0
        while True:
            doc = k.document(bot, offset, 700)
            collected += doc["body"]
            if doc["next_offset"] is None:
                break
            offset = doc["next_offset"]
        self.assertEqual(collected, body)

    def test_scope_and_empty_corpus_are_explicit(self):
        for url in ("http://core.telegram.org/api", "https://127.0.0.1/", "https://core.telegram.org.evil.test/api", "https://core.telegram.org:8443/api", "https://api.telegram.org/botTOKEN/getMe"):
            self.assertIsNone(k.canonical(url))
        self.assertFalse(k.coverage()["complete_within_discovered_scope"])
        self.assertEqual(k.canonical('https://telegram.org/blog?offset=20'), 'https://telegram.org/blog?offset=20')
        self.assertEqual(k.canonical('https://core.telegram.org/constructor/document?layer=100'), 'https://core.telegram.org/constructor/document?layer=100')
        self.assertEqual(k.search('" OR *')["results"], [])

    def test_button_search_prefers_definition_and_preserves_api_boundary(self):
        bot = 'https://core.telegram.org/bots/api'
        mtproto = 'https://core.telegram.org/method/bots.getRequestedWebViewButton'
        with k.connect() as conn:
            k.save(conn, bot, (bot, 'Telegram Bot API', '# InlineKeyboardMarkup\nSee InlineKeyboardButton.\n# InlineKeyboardButton\nstyle danger icon_custom_emoji_id', []))
            k.save(conn, mtproto, (mtproto, 'MTProto method', '# InlineKeyboardButton\nstyle danger', []))
        results = k.search('красная кнопка', 'bot-api')['results']
        self.assertEqual(results[0]['heading'], 'InlineKeyboardButton')
        self.assertTrue(all(row['url'] == bot for row in results))

    def test_mcp_protocol_roundtrip(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def run():
            params = StdioServerParameters(command=sys.executable,
                args=[str(k.ROOT / "telegram_knowledge.py"), "serve"],
                env={**os.environ, "TELEGRAM_KNOWLEDGE_DB": str(k.DB), "TELEGRAM_DOC_AUTO_SYNC": "0"})
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    self.assertEqual(len(listing.tools), 6)
                    result = await session.call_tool("get_telegram_corpus_status", {})
                    self.assertFalse(result.isError)
                    payload = result.structuredContent or json.loads(result.content[0].text)
                    self.assertEqual(payload["pages"], 0)
                    query = await session.call_tool("search_telegram_docs", {"query": "sendVideoNote"})
                    self.assertFalse(query.isError)
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()


class CliTests(unittest.TestCase):
    def test_install_subcommand_delegates_to_installer(self):
        import telegram_dev_install
        with patch.object(telegram_dev_install, "install", return_value={"ok": True}) as install, \
                patch("builtins.print"):
            k.main(["install", "--agent", "cursor", "--project", "/tmp/project", "--from", "spec"])
        install.assert_called_once_with("cursor", "/tmp/project", update=False, source="spec")

    def test_version_flag(self):
        with patch("builtins.print") as printed:
            k.main(["--version"])
        self.assertRegex(printed.call_args.args[0], r"^\d+\.\d+\.\d+")


class ToolDefinitionTests(unittest.TestCase):
    def test_every_tool_has_a_title_and_documented_parameters(self):
        async def tools():
            return await k.create_server().list_tools()
        with patch.dict(os.environ, {"TELEGRAM_DOC_AUTO_SYNC": "0"}):
            listing = asyncio.run(tools())
        self.assertEqual(len(listing), 6)
        verbs = ("search_", "get_", "list_")
        for tool in listing:
            with self.subTest(tool=tool.name):
                self.assertTrue(tool.title)
                self.assertTrue(tool.name.startswith(verbs))
                self.assertGreater(len(tool.description), 150)
                for name, schema in tool.inputSchema.get("properties", {}).items():
                    self.assertTrue(schema.get("description"), name)
        search = next(tool for tool in listing if tool.name == "search_telegram_docs")
        areas = set(search.inputSchema["properties"]["area"]["enum"])
        self.assertEqual(areas - {""}, {k.family(url) for url in k.SEEDS} | {"media-design", "gateway"})


class CachedPagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = k.DB
        k.DB = Path(self.temp.name) / "pages.sqlite3"

    def tearDown(self):
        k.DB = self.old_db
        self.temp.cleanup()

    def test_lists_cached_pages_by_area_with_paging(self):
        with k.connect() as conn:
            for url in ("https://core.telegram.org/bots/api", "https://core.telegram.org/bots/webapps",
                        "https://docs.ton.org/applications/ton-connect/overview"):
                k.save(conn, url, (url, url.rsplit("/", 1)[-1], "# Title\nSome documented text for the page.", []))
        first = k.cached_pages(limit=2)
        self.assertEqual((first["total"], len(first["pages"]), first["next_offset"]), (3, 2, 2))
        self.assertIsNone(k.cached_pages(offset=2, limit=2)["next_offset"])
        ton = k.cached_pages(area="ton")
        self.assertEqual([page["url"] for page in ton["pages"]], ["https://docs.ton.org/applications/ton-connect/overview"])
        self.assertFalse(ton["pages"][0]["freshness"]["stale"])
