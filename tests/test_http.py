import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

import httpx
import telegram_knowledge as k


class HttpTransportTests(unittest.TestCase):
    def test_remote_transport_supports_sdk_and_rejects_untrusted_hosts(self):
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "http.sqlite3"
            old_db = k.DB
            k.DB = database
            try:
                with k.connect() as conn:
                    url = "https://core.telegram.org/bots/api"
                    k.save(conn, url, (url, "Bot API", "# InlineKeyboardButton\nstyle danger icon_custom_emoji_id", []))
            finally:
                k.DB = old_db
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            base = f"http://127.0.0.1:{port}"
            with (Path(folder) / "server.log").open("w") as log:
                process = subprocess.Popen([sys.executable, str(k.ROOT / "telegram_knowledge.py"),
                    "serve", "--transport", "streamable-http", "--port", str(port)],
                    env={**os.environ, "TELEGRAM_KNOWLEDGE_DB": str(database), "TELEGRAM_DOC_AUTO_SYNC": "0"},
                    stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 20
                    while True:
                        try:
                            response = httpx.get(base + "/healthz", timeout=1)
                            response.raise_for_status()
                            break
                        except httpx.HTTPError:
                            if process.poll() is not None or time.monotonic() >= deadline:
                                self.fail("HTTP server did not start")
                            time.sleep(0.1)
                    self.assertEqual(response.json()["pages"], 1)
                    denied = httpx.post(base + "/mcp", headers={"Host": "untrusted.test"}, json={})
                    self.assertEqual(denied.status_code, 421)

                    async def roundtrip():
                        async with streamable_http_client(base + "/mcp") as (read, write, _):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                listing = await session.list_tools()
                                self.assertEqual(len(listing.tools), 5)
                                self.assertTrue(all(tool.annotations.readOnlyHint for tool in listing.tools))
                                result = await session.call_tool("search_telegram_docs", {"query": "InlineKeyboardButton", "area": "bot-api"})
                                self.assertFalse(result.isError)
                                payload = result.structuredContent or json.loads(result.content[0].text)
                                self.assertEqual(payload["results"][0]["url"], url)
                                self.assertFalse(payload["results"][0]["freshness"]["stale"])
                    asyncio.run(roundtrip())
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
