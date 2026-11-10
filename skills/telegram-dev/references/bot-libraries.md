# Bot libraries: aiogram, python-telegram-bot, grammY

Use when a project builds a bot with a library instead of raw Bot API calls: handlers, routers, filters, keyboards, conversations/FSM, sessions, middleware, webhooks, persistence, or upgrading the library.

## Indexed library documentation

| Library | Search area | Indexed source | Version the index describes |
|---|---|---|---|
| aiogram 3 (Python) | `aiogram` | https://docs.aiogram.dev/en/latest/ — dispatcher, routers, filters, FSM, middlewares, utils (keyboard builders, callback data, i18n, deep links), session, changelog, migration 2→3 | `latest`, built from the main branch; the version is in every page title ("aiogram 3.31.0 documentation") |
| python-telegram-bot (Python) | `python-telegram-bot` | https://docs.python-telegram-bot.org/en/stable/ — `telegram.ext` (Application, handlers, `ConversationHandler`, `JobQueue`, persistence, filters), `Bot`, `Message`/`CallbackQuery`/`Update` shortcuts, examples, changelog; the official wiki (guides, FAQ, design patterns) | `stable`, the latest release; the version is in every page title ("python-telegram-bot v22.8") |
| grammY (TypeScript/JavaScript) | `grammy` | https://grammy.dev/ — guide, advanced topics, plugins (keyboards, menus, conversations, sessions, runner), hosting | The current website; grammY's generated `/ref/` API reference is not indexed |

The generated per-type pages (aiogram `api/types`, `api/methods`; PTB `telegram.<Type>`) are not indexed: they mirror the Bot API, so read https://core.telegram.org/bots/api for fields and limits. Searches rank core Telegram docs first unless the query names a library (`aiogram`, `PTB`, `python-telegram-bot`, `telegram.ext`, `grammY`), so name it or pass its area.

Other libraries (Telegraf, Telethon, Pyrogram, GramJS, Kotlin/Go/Rust libraries) are not indexed. Read their official docs directly and say that the evidence did not come from the index.

## Match the installed version first

1. Find the installed version: the lock file (`uv.lock`, `poetry.lock`, `requirements*.txt` pins, `package-lock.json`, `deno.json`), or `pip show aiogram` / `npm ls grammy`. A version range in `pyproject.toml` or `package.json` is not the installed version.
2. Compare it with the version in the indexed page title. Major versions differ in kind: aiogram 2 vs 3, python-telegram-bot ≤13 (sync, `Updater`/`Dispatcher`) vs ≥20 (asyncio, `Application`). Never mix them in one answer.
3. If the indexed docs describe a newer or older version than the project uses, say so in the answer, and either read the matching pinned docs or propose an upgrade. Pinned aiogram and PTB docs can be read with `get_telegram_document`:
   - `https://docs.aiogram.dev/en/v3.20.0/dispatcher/router.html`
   - `https://docs.python-telegram-bot.org/en/v21.0/telegram.ext.conversationhandler.html`
   Pinned pages are read on demand and are not crawled. Use the version string exactly as published (`v3.20.0`, `v21.11.1`).
4. For an upgrade, read the library changelog (aiogram `changelog.html`, PTB `changelog.html`) and the migration guides (aiogram `migration_2_to_3.html`, PTB wiki `Transition-guide-to-Version-20.0`) before rewriting code.

## Compare with the Bot API

A library wraps the Bot API and can lag behind it. When a feature is new or a field is missing:

- Read the Bot API page and its changelog (https://core.telegram.org/bots/api-changelog) for the method, its parameters and the Bot API version that added it.
- Check whether the library release in use supports that Bot API version: aiogram and PTB changelogs name the Bot API version per release; grammY follows the Bot API through its `@grammyjs/types` dependency.
- If the installed version does not wrap it yet, propose an upgrade or the library's documented raw call (PTB: `Bot.do_api_request`; grammY: `bot.api.raw`; for aiogram, check its docs and changelog first). Do not switch libraries.
- Library names differ from Bot API names (`message.answer` in aiogram, `reply_text` in PTB, `ctx.reply` in grammY). Cite the library page for the call and the Bot API page for limits, permissions and field meaning.

## Common traps

- aiogram 3: handlers are registered on a `Router` included into the `Dispatcher`; callback data uses `CallbackData` factories and `F` magic filters; always answer a callback query (`callback.answer()`).
- python-telegram-bot ≥20: everything is `async`; `ConversationHandler` relies on sequential update processing; `per_message=True` changes which handlers are allowed. Check `concurrent_updates` and persistence settings before blaming Telegram.
- grammY: keyboards come from the built-in `InlineKeyboard`/`Keyboard` classes or the menu plugin; conversations and sessions are plugins with their own storage. Deno and Node imports differ.
