# Telegram Dev

[![Tests](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/telegram-dev)](https://pypi.org/project/telegram-dev/)
[![Docs monitor](https://github.com/Kay0k1/telegram-dev/actions/workflows/documentation.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/tree/docs-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Current official Telegram and TON documentation for Claude Code, Codex and Cursor.**

Telegram Dev is an MCP server plus an agent skill. The server fetches, indexes and searches the official docs and keeps them fresh: Bot API, Mini Apps, MTProto, TDLib, on the TON side docs.ton.org (TON Connect, Tolk, TVM, APIs), the TEP standards and the changelogs, and the docs of the bot libraries aiogram, python-telegram-bot and grammY. The skill teaches the agent to pick the right API, follow Telegram's rules, check library support, and cite what it read.

**Measured (Codex CLI, 11 tasks, [evals](evals/README.md)):** with Codex's own web access the plugin made no difference (45/47 rubric facts either way); with web access off, Telegram Dev kept answers current at 45/47 against 38/47 without it — Bot API 10.4 and the renamed TON coin and wallet were the gap.

[Русская версия](README.ru.md)

<!-- mcp-name: io.github.Kay0k1/telegram-dev -->

## Why

Telegram ships a new Bot API version every month or two. A model's knowledge of it stops at its training cutoff, so agents confidently write code against fields that changed or never existed. They also mix up the Bot API, MTProto and TDLib, which have very different capabilities.

TON moves just as fast. The current TON docs call the coin Gram, describe Telegram Money, the wallet built into Telegram, and treat Tolk as the main contract language with FunC as legacy. On top of that, Telegram has its own rules: blockchain features in Mini Apps must use TON and TON Connect, and digital goods are sold for Stars.

With Telegram Dev the agent reads the current page before it writes code. A real Codex CLI run in a fresh project after `uvx telegram-dev install --agent codex` (tool calls trimmed):

```text
> Use the telegram-dev skill. In a python-telegram-bot project, I want the inline
  'Delete' button to be red and show a custom emoji. Which Bot API fields do this,
  what are the requirements, and what does the request JSON look like?

  get_telegram_corpus_status {}
  search_telegram_docs {"query": "style icon_custom_emoji_id", "area": "releases"}
  search_telegram_docs {"query": "InlineKeyboardButton icon_custom_emoji_id style", "area": "bot-api"}
  get_telegram_document {"url": "https://core.telegram.org/bots/api", "offset": 167594, "length": 10500}
  get_telegram_document {"url": "https://core.telegram.org/bots/api-changelog", "offset": 39089, "length": 6000}

Use these InlineKeyboardButton fields:
- style: "danger" makes the button red.
- icon_custom_emoji_id is a custom emoji ID shown before "Delete".
- callback_data is your action identifier, 1-64 bytes.

The custom emoji requires either a bot that bought additional usernames on Fragment,
or a Premium bot owner with the message sent by the bot to a private chat, group or
supergroup. PTB 22.7+ supports both fields. Older Telegram clients show the button
unstyled. Source: https://core.telegram.org/bots/api#inlinekeyboardbutton

{"chat_id": 123456789, "text": "Choose an action:",
 "reply_markup": {"inline_keyboard": [[{"text": "Delete", "callback_data": "delete:42",
   "style": "danger", "icon_custom_emoji_id": "YOUR_CUSTOM_EMOJI_ID"}]]}}
```

The skill also knows when *not* to reach for a blockchain. Another real Codex run:

```text
> Use the telegram-dev skill. Our Telegram Mini App sells a premium in-game skin
  for 2 TON. I want a Buy button that connects the user's wallet and charges them.

  get_telegram_document {"url": "https://core.telegram.org/bots/payments-stars", "refresh": true}
  search_telegram_docs {"query": "createInvoiceLink answerPreCheckoutQuery successful_payment XTR", "area": "bot-api"}
  get_telegram_document {"url": "https://docs.ton.org/applications/ton-connect/overview", "refresh": true}
  get_telegram_document {"url": "https://core.telegram.org/bots/webapps", "offset": 40310}

Use Telegram Stars (XTR) through the Bot API. The skin is a digital good, so
Telegram requires Stars and prohibits cryptocurrency payment for this purchase.
For permitted wallet features, use the TON Connect SDK.
1. Validate initData on the backend and bind the order to the user.
2. createInvoiceLink with currency "XTR", open it with Telegram.WebApp.openInvoice.
3. Answer pre_checkout_query, grant the skin once on successful_payment,
   store telegram_payment_charge_id for refunds.
```

## Install

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). No bot token, Telegram account or API key is needed: the server only reads public documentation.

### MCP server and skill, one command

Run this in your project directory:

```sh
uvx telegram-dev install --agent claude    # or: codex, cursor
```

| `--agent` | MCP server is added to | Skill is copied to |
| --- | --- | --- |
| `claude` | `.mcp.json` | `.claude/skills/telegram-dev` |
| `codex` | `.codex/config.toml` | `.agents/skills/telegram-dev` |
| `cursor` | `.cursor/mcp.json` | `.cursor/skills/telegram-dev` |

The installer keeps your other settings, backs up the files it changes and never overwrites an existing Telegram Dev setup. The server is pinned to the installed version, so nothing has to stay on disk besides the uv cache. Open a new agent session afterwards and approve the project MCP server when asked. Codex loads project settings only after you trust the project directory.

To upgrade later: `uvx telegram-dev@latest install --agent claude --update`.

### Claude Code plugin

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

This adds the skill and the MCP server for all your projects. Use either the plugin or the installer, not both.

### MCP server only

```sh
claude mcp add --scope user telegram-knowledge -- uvx telegram-dev serve
```

```sh
codex mcp add telegram-knowledge -- uvx telegram-dev serve
```

Cursor: [![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=telegram-knowledge&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJ0ZWxlZ3JhbS1kZXYiLCJzZXJ2ZSJdfQ%3D%3D)

Any other MCP client:

```json
{
  "mcpServers": {
    "telegram-knowledge": { "command": "uvx", "args": ["telegram-dev", "serve"] }
  }
}
```

The tools work without the skill, but the skill is what makes an agent use them consistently.

## Tools

| Tool | What it does |
| --- | --- |
| `search_telegram_docs` | Full-text search over indexed sections, optionally limited to one area: `bot-api`, `mini-apps`, `telegram-api`, `tdlib`, `ton`, `releases`, `ton-releases`, `aiogram`, `python-telegram-bot`, `grammy` and others. Core Telegram docs rank first unless the query names a library |
| `get_telegram_document` | Reads an official page in pages of up to 40,000 characters; fetches it if it is missing or older than 6 hours |
| `get_telegram_corpus_status` | What is indexed, how fresh it is and which sources failed |
| `list_telegram_document_revisions` | Revisions of a page captured by this installation |
| `list_telegram_sources` | The 61 official entry points, grouped by API area |
| `list_telegram_cached_pages` | Pages already stored in the local cache, by area, with freshness |

The cache starts empty. Pages are fetched the first time the agent reads them and indexed right away. To pre-fetch everything reachable from the configured sources:

```sh
uvx telegram-dev sync --max-pages 0
uvx telegram-dev search "sendVideoNote"
uvx telegram-dev status
```

## What the skill covers

| Area | What the agent checks |
| --- | --- |
| Bot API | Messages, keyboards, updates, webhooks, files, permissions |
| Formatting and emoji | Entities, UTF-16 offsets, custom emoji and who may use them |
| Media and stickers | Voice messages, video notes, sticker sets, file limits |
| Mini Apps | JS bridge, launch parameters, themes, server-side `initData` validation |
| MTProto and TDLib | User vs bot authorization, schema and layers, TDLib versions |
| Business and payments | Business connections, Stars, subscriptions, gifts, paid media |
| Groups and channels | Admin rights, forums and topics, moderation |
| TON | Telegram's blockchain rules for Mini Apps, Stars vs crypto, TON Connect and `ton_proof`, payment processing, jettons and NFTs (TEPs), Tolk contracts, testnet first, key safety |
| Bot libraries | aiogram, python-telegram-bot and grammY: the library docs that match the installed version, compared with the Bot API page; says when the indexed docs describe another version |
| Releases | Bot API changelog, API layers, TDLib changelog, TON node and Tolk changelogs, official announcements |

The skill lives in [skills/telegram-dev](skills/telegram-dev/SKILL.md), with one reference file per area.

## How fresh the docs are

- Reading a page older than 6 hours re-fetches it. Search re-fetches up to six stale matching pages.
- While the server runs, a background cycle checks up to 120 pages every 6 hours: entry points, newly found links, oldest pages.
- If Telegram's site is unreachable, the cached text is kept and marked stale with the error, so the agent knows it is reading an old copy.
- A daily GitHub Action checks all 61 official sources and publishes hashes and errors on the [`docs-status`](https://github.com/Kay0k1/telegram-dev/tree/docs-status) branch.

Settings such as the cache path (`TELEGRAM_KNOWLEDGE_DB`) and refresh intervals are in [docs/runtime.md](docs/runtime.md).

## Self-hosting

The server also runs over Streamable HTTP, so a team can share one cache. A Dockerfile and a Caddy setup with HTTPS are included: [docs/deployment.md](docs/deployment.md).

```sh
uvx telegram-dev serve --transport streamable-http --port 8000
```

## Limits

- Search is local full-text search (SQLite FTS5), not semantic search. Exact method names and English terms work best. A small set of Russian aliases is built in.
- Coverage is what can be reached from the 61 official entry points. TON pages come from the `llms.txt` index that docs.ton.org publishes for agents, so new TON pages are picked up automatically.
- Bot libraries: guides and bot-facing references of aiogram (`latest`, built from its main branch), python-telegram-bot (`stable` docs and the official wiki) and grammY (English guides and plugins), about 250 pages. Generated per-type pages that mirror the Bot API, grammY's `/ref/` and translations are not indexed; released aiogram and PTB versions (`/en/vX.Y.Z/`) can be read on demand. Telegraf, Telethon and Pyrogram are not indexed. Page history starts when your installation first fetched the page.
- The server does not log in to Telegram, send messages, touch chats or hold wallet keys. It only reads public pages.
- The skill improves how agents work. It does not guarantee a correct answer: check the code against Telegram before shipping.

## Development

```sh
git clone https://github.com/Kay0k1/telegram-dev && cd telegram-dev
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen telegram-dev install --agent claude --project /path/to/test-project
```

CI runs the tests on Linux, macOS and Windows and checks the Docker image. [docs/validation.md](docs/validation.md) lists what has been verified by hand and what has not. Issues and pull requests are welcome; [tests/behavioral-cases.json](tests/behavioral-cases.json) has agent scenarios that still need runs in each client.

## License

[MIT](LICENSE) for the code and the skill. Fetched Telegram and TON documentation remains with its owners; the package does not bundle it ([NOTICE](NOTICE)). This is an independent project, not affiliated with Telegram or the TON Foundation.
