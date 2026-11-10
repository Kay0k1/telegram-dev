import unittest
from unittest.mock import patch

import httpx
import telegram_knowledge as k

CONNECT = "https://docs.ton.org/applications/ton-connect/overview"


def mock_client(handler):
    client = httpx.Client
    transport = httpx.MockTransport(handler)
    return patch.object(k.httpx, "Client", side_effect=lambda **kwargs: client(transport=transport, **kwargs))


class TonSourceTests(unittest.TestCase):
    def test_human_and_markdown_urls_share_one_canonical_page(self):
        for url in (CONNECT, CONNECT + "/", CONNECT + "#core",
                    "https://docs.ton.org/llms/applications/ton-connect/overview/content.md"):
            self.assertEqual(k.canonical(url), CONNECT)
        self.assertEqual(k.fetch_location(CONNECT), "https://docs.ton.org/llms/applications/ton-connect/overview/content.md")
        self.assertEqual(k.canonical("https://docs.ton.org/"), "https://docs.ton.org/llms.txt")
        self.assertEqual(k.fetch_location("https://docs.ton.org/llms.txt"), "https://docs.ton.org/llms.txt")

    def test_boundaries(self):
        for url in ("https://docs.ton.org/llms-full.txt", "https://docs.ton.org/img/logo.png",
                    "https://docs.ton.org/contribute/style-guide", "https://docs.ton.org/v3/guidelines/x",
                    "https://docs.ton.org/tolk/changelog?tab=1", "http://docs.ton.org/tolk/overview",
                    "https://ton.org/", "https://raw.githubusercontent.com/ton-blockchain/TEPs/master/scripts/x.md",
                    "https://raw.githubusercontent.com/someone/TEPs/master/text/0074-jettons-standard.md"):
            self.assertIsNone(k.canonical(url), url)
        tep = "https://raw.githubusercontent.com/ton-blockchain/TEPs/master/text/0074-jettons-standard.md"
        self.assertEqual(k.canonical(tep), tep)

    def test_areas(self):
        self.assertEqual(k.family(CONNECT), "ton")
        self.assertEqual(k.family("https://docs.ton.org/tolk/changelog"), "ton-releases")
        self.assertEqual(k.family("https://raw.githubusercontent.com/ton-blockchain/ton/master/Changelog.md"), "ton-releases")
        self.assertEqual(k.family("https://core.telegram.org/bots/blockchain-guidelines"), "ton")
        self.assertEqual(k.family("https://core.telegram.org/bots/payments-stars"), "bot-api")

    def test_markdown_page_keeps_text_title_and_in_scope_links(self):
        page = ("# TON Connect overview (https://docs.ton.org/llms/applications/ton-connect/overview/content.md)\n\n"
                "Use [Stars](https://core.telegram.org/bots/payments-stars) for digital goods. "
                "[Send](https://docs.ton.org/llms/applications/ton-connect/how-to/send-transaction/content.md) "
                "[spec](https://github.com/ton-blockchain/ton-connect) [old](https://docs.ton.org/v3/x)\n")
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, text=page, headers={"Content-Type": "text/markdown; charset=utf-8"})

        with mock_client(handler):
            url, title, body, links = k.fetch(CONNECT + "/")
        self.assertEqual(seen, ["https://docs.ton.org/llms/applications/ton-connect/overview/content.md"])
        self.assertEqual((url, title, body), (CONNECT, "TON Connect overview", page))
        self.assertEqual(links, ["https://core.telegram.org/bots/payments-stars",
                                 "https://docs.ton.org/applications/ton-connect/how-to/send-transaction"])

    def test_tep_index_links_resolve_to_raw_standards(self):
        readme = "# TON Enhancement Proposals (TEPs)\n| [Jettons](./text/0074-jettons-standard.md) |\n"
        with mock_client(lambda request: httpx.Response(200, text=readme, headers={"Content-Type": "text/plain"})):
            _, title, _, links = k.fetch("https://raw.githubusercontent.com/ton-blockchain/TEPs/master/README.md")
        self.assertEqual(title, "TON Enhancement Proposals (TEPs)")
        self.assertEqual(links, ["https://raw.githubusercontent.com/ton-blockchain/TEPs/master/text/0074-jettons-standard.md"])

    def test_html_instead_of_markdown_is_an_error(self):
        with mock_client(lambda request: httpx.Response(200, text="<html>x</html>" * 10, headers={"Content-Type": "text/html"})):
            with self.assertRaisesRegex(ValueError, "Markdown"):
                k.fetch(CONNECT)


if __name__ == "__main__":
    unittest.main()
