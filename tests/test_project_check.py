from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bot_api_schema as s
import project_check as p
from test_bot_api_schema import CHANGELOG, PAGE

PAGE_EXTRA = PAGE + """
#### answerCallbackQuery

Use this method to send answers to callback queries.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| callback\\_query\\_id | String | Yes | Unique identifier for the query to be answered |
| text | String | Optional | Text of the notification |

#### createInvoiceLink

Use this method to create a link for an invoice.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| title | String | Yes | Product name |
| currency | String | Yes | Three-letter ISO 4217 currency code |

#### close

Use this method to close the bot instance before moving it from one local server to another. Requires no parameters.
"""


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = s.parse(PAGE_EXTRA)
        cls.releases = s.parse_changelog(CHANGELOG)

    def run_on(self, files, exclude=()):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, code in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(textwrap.dedent(code), encoding="utf-8")
            return p.check_project(root, self.schema, self.releases, exclude=exclude)

    def messages(self, report):
        return [(item["severity"], item["line"], item["message"]) for item in report["findings"]]


class ProjectCheckTests(_Base):

    def test_aiogram_calls_shortcuts_and_types(self):
        report = self.run_on({"bot.py": """
            from aiogram import Bot, types
            from aiogram.types import InlineKeyboardButton

            async def handler(message: types.Message, bot: Bot):
                await message.answer("hi", reply_to_message_id=1)
                await bot.send_message(chat_id=1, text="x", disable_notification=True, colour="red")
                InlineKeyboardButton(text="Delete", callback_data="d", style="red")
                types.InlineKeyboardButton(text="Ok", callback_data="ok", style="danger")
                await bot.send_round_video(chat_id=1)
            """})
        found = self.messages(report)
        self.assertTrue(any("`reply_to_message_id` was retired in Bot API 7.0" in item[2] for item in found))
        errors = [item for item in found if item[0] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIn("style: must be one of danger, success, primary", errors[0][2])
        warnings = " ".join(item[2] for item in found if item[0] == "warning")
        self.assertIn("`colour` is not a Bot API parameter of sendMessage", warnings)
        self.assertIn("no method `sendRoundVideo`", warnings)
        self.assertEqual(report["errors"], 1)
        self.assertEqual(report["files_scanned"], 1)

    def test_project_models_and_other_libraries_are_ignored(self):
        report = self.run_on({"models.py": """
            from aiogram import Router
            from telegram.ext import filters
            from app.db import User

            def build():
                User(telegram_id=1, balance_kopeks=5)
                filters.User(user_id=[1])
                websocket.close(code=1000, reason="bye")
                self.send_message(message="hello")
            """})
        self.assertEqual(report["findings"], [])

    def test_retired_names_are_reported_on_any_receiver(self):
        report = self.run_on({"wrap.py": """
            import telebot
            def notify(bot_wrapper, chat):
                bot_wrapper.send_message(chat, "hi", reply_to_message_id=3, row_width=2, read_timeout=5)
            """})
        found = self.messages(report)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0][2].startswith("`reply_to_message_id` was retired in Bot API 7.0: Added the class ReplyParameters"))

    def test_raw_http_calls(self):
        report = self.run_on({"raw.py": """
            import httpx
            TOKEN = "x"
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": 1, "text": "Pick", "reply_markup": {"inline_keyboard": [[{"text": "A", "callback_data": "a", "style": "red"}]]},
                "reply_to_message_id": 5, "colour": 1})
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendRoundVideo", json={"chat_id": 1})
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json={"anything": 1})
            """})
        found = self.messages(report)
        errors = [item[2] for item in found if item[0] == "error"]
        self.assertTrue(any("style: must be one of" in error for error in errors))
        self.assertTrue(any("no parameter 'colour'" in error for error in errors))
        self.assertTrue(any("no method `sendRoundVideo`" in error for error in errors))
        self.assertTrue(any("Bot API 7.0" in item[2] for item in found if item[0] == "warning"))

    def test_shortcut_answer_accepts_any_candidate(self):
        report = self.run_on({"cb.py": """
            from aiogram import types
            async def on_click(callback: types.CallbackQuery):
                await callback.answer(text="Done", callback_query_id="1")
                await callback.answer(show_alert=True)
            """})
        self.assertEqual(report["findings"], [])

    def test_exclude_libraries_and_syntax_errors(self):
        report = self.run_on({
            "tests/test_kb.py": "from aiogram.types import InlineKeyboardButton\nInlineKeyboardButton(text='a', style='rainbow')\n",
            "broken.py": "from aiogram import Bot\ndef (:\n",
            "requirements.txt": "aiogram==3.31.0\nhttpx>=0.28\n",
            "pyproject.toml": '[project]\ndependencies = ["python-telegram-bot[job-queue]>=21.0"]\n',
            "sub/pyproject.toml": '[tool.poetry.dependencies]\naiogram = "^3.4"\n',
        }, exclude=["tests/*"])
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["skipped"][0]["file"], "broken.py")
        self.assertEqual(report["libraries"], {"aiogram": ["==3.31.0", "^3.4"], "python-telegram-bot": [">=21.0"]})
        self.assertIn("Bot API 10.4", p.format_report(report))

    def test_github_annotations(self):
        report = self.run_on({"bot.py": "from aiogram.types import InlineKeyboardButton\nInlineKeyboardButton(text='a', style='red')\n"})
        lines = p.format_report(report, "github").splitlines()
        self.assertTrue(lines[0].startswith("::error file=bot.py,line=2,title=telegram-dev::"))


if __name__ == "__main__":
    unittest.main()


class ReviewRegressionTests(_Base):
    def test_raw_requests_that_work_are_not_errors(self):
        report = self.run_on({"raw.py": """
            import requests, httpx
            T = "x"
            requests.post(f"https://api.telegram.org/bot{T}/sendMediaGroup", data={"chat_id": 1}, files={"m": open("a", "rb")})
            requests.post(f"https://api.telegram.org/bot{T}/sendmessage", data={"chat_id": "1", "text": "x", "disable_notification": "True"})
            httpx.post(f"https://api.telegram.org/bot{T}/sendMessage", json={"chat_id": 1, "text": "x",
                       "reply_markup": {"inline_keyboard": [[{"text": label, "callback_data": "x"}]]}})
            requests.post(f"https://api.telegram.org/bot{T}/sendMessage", params={"chat_id": 1}, json={"text": "x"})
            """})
        self.assertEqual([item for item in report["findings"] if item["severity"] == "error"], [])

    def test_unreadable_files_are_reported_not_fatal(self):
        deep = "from aiogram import Bot\nx = " + " + ".join(['"a"'] * 3000) + "\n"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "bom.py").write_bytes("﻿from aiogram.types import InlineKeyboardButton\nInlineKeyboardButton(text='a', style='red')\n".encode("utf-8"))
            (root / "deep.py").write_text(deep, encoding="utf-8")
            report = p.check_project(root, self.schema, self.releases)
        self.assertEqual(report["errors"], 1, "a file with a byte order mark is analysed")
        self.assertEqual([item["file"] for item in report["skipped"]], ["deep.py"])
        self.assertIn("1 files not analysed (deep.py)", p.format_report(report))

    def test_library_classes_options_and_receivers(self):
        report = self.run_on({"misc.py": """
            from aiogram import Bot
            import telegram
            Bot.set_current(bot)
            Bot.get_current()
            bot.send_media_group(chat_id=1, media=[], caption="all", parse_mode="HTML")
            checkbox.button(label="x")
            """})
        self.assertEqual(report["findings"], [])

    def test_exclude_matches_paths_relative_to_root(self):
        files = {"tests/sub/a.py": "from aiogram.types import InlineKeyboardButton\nInlineKeyboardButton(text='a', style='red')\n",
                 "app/tests.py": "from aiogram.types import InlineKeyboardButton\nInlineKeyboardButton(text='a', style='red')\n"}
        report = self.run_on(files, exclude=["tests/*"])
        self.assertEqual([item["file"] for item in report["findings"]], ["app/tests.py"])

    def test_annotation_properties_are_escaped(self):
        report = {"findings": [{"file": "a,b:c.py", "line": 3, "severity": "warning", "call": "x", "message": "m"}],
                  "bot_api_version": "10.4", "errors": 0, "warnings": 1, "files_scanned": 1, "skipped": [], "truncated": False}
        self.assertTrue(p.format_report(report, "github", "src").startswith("::warning file=src/a%2Cb%3Ac.py,line=3,"))
