import unittest
from unittest.mock import patch

import httpx
import telegram_knowledge as k


class FetchTests(unittest.TestCase):
    def test_wrapper_retains_sections_after_early_content_closing_tag(self):
        html = '''<html><title>Secret Chats</title><body>
        <nav>irrelevant navigation</nav><div id="dev_page_content_wrap">
        <h1>Secret Chats</h1><div id="dev_page_content"><p>Introductory material about encryption.</p></div>
        <h2>Key Generation</h2><p>Important key exchange instructions after the early closing div.</p>
        <h2>Sending Messages</h2><p>Encrypted messages and key rotation.</p>
        </div><footer>irrelevant footer</footer></body></html>'''
        client = httpx.Client
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text=html, headers={"Content-Type": "text/html"}))
        with patch.object(k.httpx, "Client", side_effect=lambda **kwargs: client(transport=transport, **kwargs)):
            _, _, body, _ = k.fetch("https://core.telegram.org/api/end-to-end")
        self.assertIn("Key Generation", body)
        self.assertIn("Sending Messages", body)
        self.assertNotIn("irrelevant", body)

    def test_login_remains_web_integration_and_mtproto_bot_methods_remain_client_api(self):
        self.assertEqual(k.family("https://core.telegram.org/bots/telegram-login"), "web-integrations")
        self.assertEqual(k.family("https://core.telegram.org/method/bots.getBotInfo"), "telegram-api")
        self.assertEqual(k.family("https://core.telegram.org/bots/api"), "bot-api")

    def test_pinned_official_schema_is_allowed_without_widening_repository_scope(self):
        sha = "a" * 40
        pinned = f"https://raw.githubusercontent.com/tdlib/td/{sha}/td/generate/scheme/td_api.tl"
        self.assertEqual(k.canonical(pinned), pinned)
        self.assertIsNone(k.canonical(pinned.replace('/tdlib/td/', '/untrusted/td/')))
        self.assertIsNone(k.canonical(pinned.replace(sha, 'unreviewed-branch')))
        self.assertIsNone(k.canonical(pinned.replace('td_api.tl', 'private.txt')))


if __name__ == "__main__":
    unittest.main()
