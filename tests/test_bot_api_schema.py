import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bot_api_schema as s
import telegram_knowledge as k

API = "https://core.telegram.org/bots/api"
# A small page written in the same Markdown shape as the cached Bot API page.
PAGE = """# Telegram Bot API

### Recent changes

#### November 9, 2026

**Bot API 10.4**

* Added the method [sendWidget](https://core.telegram.org/bots/api#sendwidget).

### Available types

#### InlineKeyboardButton

This object represents one button of an inline keyboard.

| Field | Type | Description |
| --- | --- | --- |
| text | String | Label text on the button |
| style | String | *Optional*. Style of the button. Must be one of “danger” (red), “success” (green) or “primary” (blue). |
| callback\\_data | String | *Optional*. Data to be sent in a [callback query](https://core.telegram.org/bots/api#callbackquery), 1-64 bytes |

#### InlineKeyboardMarkup

This object represents an inline keyboard.

| Field | Type | Description |
| --- | --- | --- |
| inline\\_keyboard | Array of Array of [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton) | Array of button rows |

#### ForceReply

Shows a reply interface.

| Field | Type | Description |
| --- | --- | --- |
| force\\_reply | True | Shows reply interface to the user |

#### InputMedia

This object represents the content of a media message to be sent. It should be one of

* [InputMediaPhoto](https://core.telegram.org/bots/api#inputmediaphoto)
* [InputMediaVideo](https://core.telegram.org/bots/api#inputmediavideo)

#### InputMediaPhoto

Represents a photo to be sent.

| Field | Type | Description |
| --- | --- | --- |
| type | String | Type of the result, must be *photo* |
| media | String | File to send |

#### InputMediaVideo

Represents a video to be sent.

| Field | Type | Description |
| --- | --- | --- |
| type | String | Type of the result, must be *video* |
| media | String | File to send |
| supports\\_streaming | Boolean | *Optional*. Pass *True* if the uploaded video is suitable for streaming |

### Available methods

#### sendMessage

Use this method to send text messages. On success, the sent [Message](https://core.telegram.org/bots/api#message) is returned.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| chat\\_id | Integer or String | Optional | Unique identifier for the target chat; required unless the message is sent as an ephemeral reply to a callback query |
| text | String | Yes | Text of the message to be sent, 1-4096 characters after entities parsing |
| disable\\_notification | Boolean | Optional | Sends the message silently |
| reply\\_markup | [InlineKeyboardMarkup](https://core.telegram.org/bots/api#inlinekeyboardmarkup) or [ForceReply](https://core.telegram.org/bots/api#forcereply) | Optional | Additional interface options |

#### sendMediaGroup

Use this method to send a group of photos or videos as an album.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| chat\\_id | Integer or String | Yes | Unique identifier for the target chat |
| media | Array of [InputMediaPhoto](https://core.telegram.org/bots/api#inputmediaphoto) and [InputMediaVideo](https://core.telegram.org/bots/api#inputmediavideo) | Yes | A JSON-serialized array describing messages to be sent |

#### getMe

A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a [User](https://core.telegram.org/bots/api#user) object.
"""
CHANGELOG = """# Bot API changelog

### 2026

#### November 9, 2026

**Bot API 10.4**

**Widgets**

* Added the method [sendWidget](https://core.telegram.org/bots/api#sendwidget).

#### February 9, 2026

**Bot API 9.4**

* Added the field *style* to the classes [KeyboardButton](https://core.telegram.org/bots/api#keyboardbutton) and [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton).

### 2023

#### December 29, 2023

**Bot API 7.0**

* Added the class [ReplyParameters](https://core.telegram.org/bots/api#replyparameters) and replaced parameters *reply\\_to\\_message\\_id* and *allow\\_sending\\_without\\_reply* in the methods [sendMessage](https://core.telegram.org/bots/api#sendmessage) with the field *reply\\_parameters*.
"""


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = s.parse(PAGE)
        cls.releases = s.parse_changelog(CHANGELOG)

    def check(self, method, params):
        return s.check(self.schema, method, params, self.releases)

    def test_parse_methods_types_and_constraints(self):
        self.assertEqual(self.schema["version"], "10.4")
        self.assertEqual(set(self.schema["methods"]), {"sendMessage", "sendMediaGroup", "getMe"})
        send = self.schema["methods"]["sendMessage"]
        self.assertEqual(send["returns"], "On success, the sent Message is returned.")
        self.assertTrue(send["params"]["text"]["required"])
        self.assertFalse(send["params"]["chat_id"]["required"])
        self.assertIn("required unless", send["params"]["chat_id"]["required_unless"])
        button = self.schema["types"]["InlineKeyboardButton"]["fields"]
        self.assertEqual(button["style"]["enum"], ["danger", "success", "primary"])
        self.assertEqual(button["callback_data"]["length"], {"min": 1, "max": 64, "unit": "bytes"})
        self.assertFalse(button["style"]["required"])
        self.assertEqual(self.schema["types"]["InputMediaPhoto"]["fields"]["type"]["const"], "photo")
        self.assertEqual(self.schema["types"]["InputMedia"]["one_of"], ["InputMediaPhoto", "InputMediaVideo"])
        self.assertEqual(self.schema["methods"]["getMe"]["params"], {})

    def test_valid_call_with_nested_markup(self):
        result = self.check("sendMessage", {"chat_id": 1, "text": "Pick", "reply_markup": {
            "inline_keyboard": [[{"text": "Delete", "callback_data": "del:1", "style": "danger"}]]}})
        self.assertEqual((result["valid"], result["errors"], result["warnings"]), (True, [], []))

    def test_json_string_markup_and_union_alternative(self):
        self.assertTrue(self.check("sendMessage", {"chat_id": "@channel", "text": "x",
                                                   "reply_markup": json.dumps({"force_reply": True})})["valid"])

    def test_errors_for_invented_and_wrong_values(self):
        result = self.check("sendMessage", {"chat_id": 1, "text": "x", "reply_markup": {
            "inline_keyboard": [[{"text": "A", "style": "red", "colour": "red"}]]}})
        messages = {error["path"]: error["message"] for error in result["errors"]}
        self.assertFalse(result["valid"])
        self.assertIn("danger, success, primary", messages["reply_markup.inline_keyboard[0][0].style"])
        self.assertIn("no field 'colour'", messages["reply_markup.inline_keyboard[0][0].colour"])
        missing = self.check("sendMessage", {"chat_id": 1})
        self.assertEqual(missing["errors"][0]["path"], "text")
        self.assertIn("did you mean text", self.check("sendMessage", {"chat_id": 1, "txt": "x", "text": "y"})["errors"][0]["message"])

    def test_union_discriminator(self):
        ok = self.check("sendMediaGroup", {"chat_id": 1, "media": [{"type": "photo", "media": "a"},
                                                                   {"type": "video", "media": "b", "supports_streaming": True}]})
        self.assertTrue(ok["valid"])
        wrong = self.check("sendMediaGroup", {"chat_id": 1, "media": [{"type": "sticker", "media": "a"}]})
        self.assertEqual(wrong["errors"], [{"path": "media[0].type", "message": "must be one of photo, video"}])
        mixed = self.check("sendMediaGroup", {"chat_id": 1, "media": [{"type": "photo", "media": "a", "supports_streaming": True}]})
        self.assertIn("InputMediaPhoto has no field 'supports_streaming'", mixed["errors"][0]["message"])

    def test_warnings_do_not_invalidate(self):
        result = self.check("sendMessage", {"chat_id": "123", "text": "x", "disable_notification": "true",
                                            "reply_to_message_id": 5, "reply_markup": {"inline_keyboard": [[{"text": "A", "callback_data": "x" * 70}]]}})
        self.assertTrue(result["valid"])
        warnings = {warning["path"]: warning["message"] for warning in result["warnings"]}
        self.assertIn("Boolean sent as a string", warnings["disable_notification"])
        self.assertIn("Bot API 7.0", warnings["reply_to_message_id"])
        self.assertIn("70 bytes", warnings["reply_markup.inline_keyboard[0][0].callback_data"])
        self.assertNotIn("chat_id", warnings, "a chat username or numeric string is a valid String")
        self.assertIn("fine only if this does not apply: required unless", self.check("sendMessage", {"text": "x"})["warnings"][0]["message"])

    def test_method_names(self):
        self.assertIn("use sendMessage", self.check("sendmessage", {})["errors"][0]["message"])
        self.assertIn("did you mean sendMediaGroup", self.check("sendMediaGrup", {})["errors"][0]["message"])
        self.assertTrue(self.check("getMe", {})["valid"])

    def test_definition_lookup(self):
        self.assertEqual(s.definition(self.schema, "inlinekeyboardbutton")["kind"], "type")
        self.assertEqual(s.definition(self.schema, "sendMessage")["kind"], "method")
        self.assertIn("sendMessage", s.definition(self.schema, "sendMesage")["suggestions"])

    def test_changelog(self):
        self.assertEqual([release["version"] for release in self.releases], ["10.4", "9.4", "7.0"])
        self.assertEqual(self.releases[0]["url"], "https://core.telegram.org/bots/api-changelog#november-9-2026")
        self.assertEqual(self.releases[0]["changes"][0]["topic"], "Widgets")
        self.assertEqual([r["version"] for r in s.changes(self.releases, since="9.0")], ["10.4", "9.4"])
        self.assertEqual([r["version"] for r in s.changes(self.releases, name="InlineKeyboardButton")], ["9.4"])
        self.assertEqual([r["version"] for r in s.changes(self.releases, name="reply_to_message_id")], ["7.0"])
        self.assertIsNone(s.retired(self.releases, "sendMessage", "colour"))


class ServerSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = k.DB
        k.DB = Path(self.temp.name) / "schema.sqlite3"
        with k.connect() as conn:
            k.save(conn, s.PAGE, (s.PAGE, "Telegram Bot API", PAGE, []))
            k.save(conn, s.CHANGELOG, (s.CHANGELOG, "Bot API changelog", CHANGELOG, []))
        k._schema_cache.clear()

    def tearDown(self):
        k.DB = self.old_db
        k._schema_cache.clear()
        self.temp.cleanup()

    def test_tools_use_cached_pages(self):
        definition = k.bot_api_definition("InlineKeyboardButton")
        self.assertEqual(definition["bot_api_version"], "10.4")
        self.assertEqual(definition["changes"][0]["version"], "9.4")
        self.assertFalse(definition["freshness"]["stale"])
        self.assertFalse(k.check_bot_api("sendMessage", {"chat_id": 1})["valid"])
        changes = k.bot_api_changes(since="9.4")
        self.assertEqual(changes["current_version"], "10.4")
        self.assertEqual([release["version"] for release in changes["releases"]], ["10.4"])


if __name__ == "__main__":
    unittest.main()
