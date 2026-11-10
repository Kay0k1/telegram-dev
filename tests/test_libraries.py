from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import telegram_knowledge as k

AIOGRAM = "https://docs.aiogram.dev/en/latest/"
PTB = "https://docs.python-telegram-bot.org/en/stable/"
WIKI = "https://github.com/python-telegram-bot/python-telegram-bot/wiki/"
WIKI_RAW = "https://raw.githubusercontent.com/wiki/python-telegram-bot/python-telegram-bot/"
GRAMMY_RAW = "https://raw.githubusercontent.com/grammyjs/website/main/site/docs/"


def mock_client(handler):
    client = httpx.Client
    transport = httpx.MockTransport(handler)
    return patch.object(k.httpx, "Client", side_effect=lambda **kwargs: client(transport=transport, **kwargs))


class LibraryBoundaryTests(unittest.TestCase):
    def test_library_seeds_are_canonical_and_in_their_areas(self):
        areas = {"https://docs.aiogram.dev/en/latest/": "aiogram",
                 "https://docs.python-telegram-bot.org/en/stable/": "python-telegram-bot",
                 WIKI_RAW + "_Sidebar.md": "python-telegram-bot",
                 "https://grammy.dev/sitemap.xml": "grammy"}
        for url, area in areas.items():
            self.assertIn(url, k.SEEDS)
            self.assertEqual(k.canonical(url), url)
            self.assertEqual(k.family(url), area)

    def test_aiogram_guides_and_dispatcher_reference_only(self):
        same = {AIOGRAM + "index.html": AIOGRAM, "https://docs.aiogram.dev/en/latest": AIOGRAM,
                AIOGRAM + "dispatcher/index.html": AIOGRAM + "dispatcher/",
                AIOGRAM + "dispatcher/router.html#aiogram.dispatcher.router.Router": AIOGRAM + "dispatcher/router.html",
                AIOGRAM + "utils/keyboard.html": AIOGRAM + "utils/keyboard.html",
                "https://docs.aiogram.dev/en/v3.20.0/dispatcher/router.html": "https://docs.aiogram.dev/en/v3.20.0/dispatcher/router.html"}
        for url, expected in same.items():
            self.assertEqual(k.canonical(url), expected, url)
            self.assertEqual(k.family(expected), "aiogram")
        for url in (AIOGRAM + "api/types/message.html", AIOGRAM + "api/methods/send_message.html",
                    AIOGRAM + "api/enums/chat_type.html", AIOGRAM + "api/", AIOGRAM + "api/index.html", AIOGRAM + "_modules/aiogram/dispatcher/router.html",
                    AIOGRAM + "_static/basic.css", AIOGRAM + "_sources/index.rst.txt", AIOGRAM + "genindex.html",
                    AIOGRAM + "search.html?q=router", AIOGRAM + "dispatcher/router.html?highlight=x",
                    "https://docs.aiogram.dev/en/dev-3.x/", "https://docs.aiogram.dev/uk_UA/latest/",
                    "https://docs.aiogram.dev/", "http://docs.aiogram.dev/en/latest/"):
            self.assertIsNone(k.canonical(url), url)

    def test_python_telegram_bot_ext_reference_examples_and_wiki(self):
        same = {PTB + "index.html": PTB,
                PTB + "telegram.ext.conversationhandler.html": PTB + "telegram.ext.conversationhandler.html",
                PTB + "telegram.ext.html": PTB + "telegram.ext.html",
                PTB + "telegram.bot.html#telegram.Bot.send_message": PTB + "telegram.bot.html",
                PTB + "examples.conversationbot.html": PTB + "examples.conversationbot.html",
                "https://docs.python-telegram-bot.org/en/v21.0/telegram.bot.html": "https://docs.python-telegram-bot.org/en/v21.0/telegram.bot.html",
                WIKI.rstrip("/"): WIKI + "Home", WIKI: WIKI + "Home",
                WIKI + "Storing-bot,-user-and-chat-related-data": WIKI + "Storing-bot,-user-and-chat-related-data",
                WIKI_RAW + "Concurrency.md": WIKI + "Concurrency"}
        for url, expected in same.items():
            self.assertEqual(k.canonical(url), expected, url)
            self.assertEqual(k.family(expected), "python-telegram-bot")
        # telegram.externalreplyinfo shares the "telegram.ext" prefix but is a Bot API type mirror.
        for url in (PTB + "telegram.externalreplyinfo.html", PTB + "telegram.chat.html", PTB + "coc.html",
                    PTB + "inclusions/bot_methods.html", PTB + "_static/x.js",
                    "https://docs.python-telegram-bot.org/en/latest/telegram.bot.html",
                    WIKI + "_Sidebar", WIKI + "Press", WIKI + "Home/_history",
                    "https://github.com/python-telegram-bot/python-telegram-bot/issues",
                    "https://github.com/someone/python-telegram-bot/wiki/Home",
                    "https://raw.githubusercontent.com/wiki/someone/python-telegram-bot/Home.md"):
            self.assertIsNone(k.canonical(url), url)
        self.assertEqual(k.fetch_location(WIKI + "Concurrency"), WIKI_RAW + "Concurrency.md")

    def test_grammy_english_guides_without_generated_reference(self):
        same = {"https://grammy.dev/guide": "https://grammy.dev/guide/",
                "https://grammy.dev/guide/index": "https://grammy.dev/guide/",
                "https://grammy.dev/plugins/keyboard.html": "https://grammy.dev/plugins/keyboard",
                "https://grammy.dev/plugins/keyboard#inline-keyboards": "https://grammy.dev/plugins/keyboard",
                GRAMMY_RAW + "plugins/keyboard.md": "https://grammy.dev/plugins/keyboard",
                GRAMMY_RAW + "guide/README.md": "https://grammy.dev/guide/"}
        for url, expected in same.items():
            self.assertEqual(k.canonical(url), expected, url)
            self.assertEqual(k.family(expected), "grammy")
        for url in ("https://grammy.dev/", "https://grammy.dev/ref/core/bot", "https://grammy.dev/es/guide/",
                    "https://grammy.dev/zh/plugins/keyboard", "https://grammy.dev/guide/basics?x=1",
                    "https://grammy.dev/images/logo.png", "https://grammy.dev/guide/a/b",
                    GRAMMY_RAW + "ref/core.md", "https://raw.githubusercontent.com/grammyjs/website/dev/site/docs/guide/basics.md"):
            self.assertIsNone(k.canonical(url), url)
        self.assertEqual(k.fetch_location("https://grammy.dev/guide/"), GRAMMY_RAW + "guide/README.md")
        self.assertEqual(k.fetch_location("https://grammy.dev/plugins/keyboard"), GRAMMY_RAW + "plugins/keyboard.md")
        self.assertEqual(k.fetch_location("https://grammy.dev/sitemap.xml"), "https://grammy.dev/sitemap.xml")


class LibraryFetchTests(unittest.TestCase):
    def test_sphinx_page_drops_anchors_and_source_links(self):
        html = f'''<html><title>Router - aiogram 3.31.0 documentation</title><body>
        <div class="sidebar-tree"><a href="../api/types/message.html">Message</a><a href="webhook.html">Webhook</a></div>
        <article role="main"><h1>Router<a class="headerlink" href="#router">¶</a></h1>
        <p>Use <code>@router.callback_query()</code> to handle callback queries.</p>
        <a class="reference internal" href="../_modules/aiogram/dispatcher/router.html#Router"><span class="viewcode-link"><span class="pre">[source]</span></span></a>
        <a href="filters/callback_data.html">Callback data</a> <a href="../api/types/callback_query.html">CallbackQuery</a>
        </article></body></html>'''
        with mock_client(lambda request: httpx.Response(200, text=html, headers={"Content-Type": "text/html"})):
            url, title, body, links = k.fetch(AIOGRAM + "dispatcher/router.html")
        self.assertEqual(title, "Router - aiogram 3.31.0 documentation")
        self.assertTrue(body.startswith("# Router\n"), body)
        self.assertNotIn("¶", body)
        self.assertNotIn("[source]", body)
        # The sidebar table of contents is followed; generated type mirrors and [source] pages are not.
        self.assertEqual(links, [AIOGRAM + "dispatcher/filters/callback_data.html", AIOGRAM + "dispatcher/router.html",
                                 AIOGRAM + "dispatcher/webhook.html"])

    def test_pinned_version_is_read_but_not_crawled(self):
        pinned = "https://docs.aiogram.dev/en/v3.20.0/dispatcher/router.html"
        html = '<html><title>Router - aiogram 3.20.0</title><article><h1>Router</h1><p>Routers in 3.20.</p><a href="errors.html">Errors</a></article></html>'
        with mock_client(lambda request: httpx.Response(200, text=html, headers={"Content-Type": "text/html"})):
            result = k.fetch(pinned)
        self.assertEqual(result[0], pinned)
        self.assertEqual(k.pinned_library_version(pinned), "v3.20.0")
        self.assertIsNone(k.pinned_library_version(AIOGRAM + "dispatcher/router.html"))
        current = PTB + "changelog.html"
        with tempfile.TemporaryDirectory() as temp, patch.object(k, "DB", Path(temp) / "db.sqlite3"):
            with k.connect() as conn:
                k.save(conn, pinned, result)
                k.save(conn, current, (current, "Changelog", "# Changelog\nSee the v21.7 docs.",
                                       ["https://docs.python-telegram-bot.org/en/v21.7/telegram.bot.html", PTB + "telegram.bot.html"]))
                pending = [row[0] for row in conn.execute("SELECT url FROM frontier WHERE state='pending'")]
        # Neither the pinned page's own links nor links to other pinned versions are crawled.
        self.assertEqual(pending, [PTB + "telegram.bot.html"])

    def test_grammy_reads_markdown_twin_with_front_matter(self):
        page = ("---\nprev: false\nnext: false\n---\n\n# Inline and Custom Keyboards (built-in)\n\n"
                "Build an [inline keyboard](#inline-keyboards) with `new InlineKeyboard()`. "
                "See [menus](./menu) and [Bot API](https://core.telegram.org/bots/features#inline-keyboards) "
                "and [ref](/ref/core/inlinekeyboard).\n")
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, text=page, headers={"Content-Type": "text/plain; charset=utf-8"})

        with mock_client(handler):
            url, title, body, links = k.fetch("https://grammy.dev/plugins/keyboard.html")
        self.assertEqual(seen, [GRAMMY_RAW + "plugins/keyboard.md"])
        self.assertEqual((url, title, body), ("https://grammy.dev/plugins/keyboard", "Inline and Custom Keyboards (built-in) - grammY", page))
        self.assertEqual(links, ["https://core.telegram.org/bots/features", "https://grammy.dev/plugins/menu"])

    def test_grammy_sitemap_feeds_discovery_only(self):
        sitemap = ('<?xml version="1.0"?><urlset><url><loc>https://grammy.dev/guide/index</loc></url>'
                   '<url><loc>https://grammy.dev/plugins/keyboard</loc></url><url><loc>https://grammy.dev/ref/core/bot</loc></url>'
                   '<url><loc>https://grammy.dev/es/guide/</loc></url></urlset>')
        with mock_client(lambda request: httpx.Response(200, text=sitemap, headers={"Content-Type": "application/xml"})):
            result = k.fetch("https://grammy.dev/sitemap.xml")
        self.assertEqual(result[3], ["https://grammy.dev/guide/", "https://grammy.dev/plugins/keyboard"])
        self.assertEqual(result[1], "grammY documentation index")
        with tempfile.TemporaryDirectory() as temp, patch.object(k, "DB", Path(temp) / "db.sqlite3"):
            with k.connect() as conn:
                k.save(conn, result[0], result)
                self.assertEqual(conn.execute("SELECT count(*) FROM chunks").fetchone()[0], 0)
                pending = {row[0] for row in conn.execute("SELECT url FROM frontier WHERE state='pending'")}
            self.assertEqual(pending, set(result[3]))

    def test_wiki_sidebar_resolves_wiki_links_to_human_urls(self):
        sidebar = ("## Must read\n1. [[Introduction to the API|Introduction-to-the-API]]\n"
                   "2. [Builder Pattern for `Application`](Builder-Pattern)\n3. [[Working with Files and Media]]\n"
                   "- [[How To Release|Releasing-a-new-version]]\n")
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, text=sidebar, headers={"Content-Type": "text/plain; charset=utf-8"})

        with mock_client(handler):
            url, title, body, links = k.fetch(WIKI_RAW + "_Sidebar.md")
        self.assertEqual(seen, [WIKI_RAW + "_Sidebar.md"])
        self.assertEqual(title, "python-telegram-bot wiki documentation index")
        self.assertEqual(links, [WIKI + "Builder-Pattern", WIKI + "Introduction-to-the-API", WIKI + "Working-with-Files-and-Media"])

    def test_wiki_page_is_titled_by_its_name(self):
        with mock_client(lambda request: httpx.Response(200, text="Use `ConversationHandler` with care. " * 3, headers={"Content-Type": "text/plain"})):
            url, title, _, _ = k.fetch(WIKI + "Concurrency")
        self.assertEqual((url, title), (WIKI + "Concurrency", "Concurrency - python-telegram-bot wiki"))
        page = "# Introduction\nThe JobQueue runs callbacks later."
        with mock_client(lambda request: httpx.Response(200, text=page, headers={"Content-Type": "text/plain"})):
            _, title, _, _ = k.fetch(WIKI + "Extensions---JobQueue")
        self.assertEqual(title, "Extensions – JobQueue - python-telegram-bot wiki")

    def test_html_instead_of_markdown_is_an_error(self):
        with mock_client(lambda request: httpx.Response(200, text="<html>x</html>" * 10, headers={"Content-Type": "text/html"})):
            with self.assertRaisesRegex(ValueError, "Markdown"):
                k.fetch("https://grammy.dev/guide/basics")


class LibrarySearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = patch.object(k, "DB", Path(self.temp.name) / "db.sqlite3")
        self.db.start()
        pages = {
            "https://core.telegram.org/bots/api": ("Telegram Bot API", "# InlineKeyboardMarkup\nThis object represents an inline keyboard. Callback query handler data."),
            "https://core.telegram.org/bots/features": ("Bots: An introduction", "# Inline keyboards\nInline keyboard buttons send a callback query."),
            AIOGRAM + "dispatcher/router.html": ("Router - aiogram 3.31.0 documentation", "# Router\nRegister a callback query handler with @router.callback_query(). Inline keyboard."),
            PTB + "telegram.ext.conversationhandler.html": ("ConversationHandler - python-telegram-bot v22.8", "# ConversationHandler\nA handler to hold a conversation. Callback query handler states. Inline keyboard."),
            "https://grammy.dev/plugins/keyboard": ("Inline and Custom Keyboards (built-in) - grammY", "# Inline Keyboards\nBuild an inline keyboard with new InlineKeyboard(). Callback query handler."),
        }
        with k.connect() as conn:
            for url, (title, body) in pages.items():
                k.save(conn, url, (url, title, body, []))

    def tearDown(self):
        self.db.stop()
        self.temp.cleanup()

    def families(self, query, area=""):
        return [row["family"] for row in k.search(query, area=area, limit=10)["results"]]

    def test_core_docs_rank_first_without_a_library_name(self):
        families = self.families("inline keyboard")
        self.assertEqual(set(families[:2]), {"bot-api"})
        self.assertEqual(set(families[2:]), {"aiogram", "python-telegram-bot", "grammy"})

    def test_named_library_ranks_first_and_name_is_not_a_required_term(self):
        self.assertEqual(self.families("aiogram 3 callback query handler")[0], "aiogram")
        self.assertEqual(self.families("PTB ConversationHandler"), ["python-telegram-bot"])
        self.assertEqual(self.families("python-telegram-bot v22 callback query handler")[0], "python-telegram-bot")
        self.assertEqual(self.families("telegram.ext.ConversationHandler"), ["python-telegram-bot"])
        families = self.families("grammY inline keyboard")
        self.assertEqual(families[0], "grammy")
        self.assertEqual(families[1:3], ["bot-api", "bot-api"])

    def test_library_area_filters(self):
        self.assertEqual(set(self.families("inline keyboard", area="grammy")), {"grammy"})
        self.assertEqual(set(self.families("inline keyboard", area="grammY")), {"grammy"})

    def test_named_libraries(self):
        self.assertEqual(k.named_libraries("aiogram 3.x callback")[0], ["aiogram"])
        self.assertEqual(k.named_libraries("PTB v21.0 JobQueue")[0], ["python-telegram-bot"])
        self.assertEqual(k.named_libraries("grammY menu")[0], ["grammy"])
        self.assertEqual(k.named_libraries("inline keyboard")[0], [])
        self.assertEqual(k.named_libraries("aptbx telegram.extension")[0], [])


if __name__ == "__main__":
    unittest.main()
