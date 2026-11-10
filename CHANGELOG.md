# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/).

## [0.9.0] - 2026-11-11

### Added

- `telegram-dev check [PATH]`: checks every Bot API call in a Python bot project (aiogram, python-telegram-bot, pyTelegramBotAPI, raw HTTP requests to api.telegram.org) against the current official schema in one run and prints only findings. Errors: values outside the documented list, unknown methods or parameters in raw API requests. Warnings: parameters Telegram retired, with the version and changelog entry that replaced them; keyword arguments that are neither Bot API parameters nor known library options; bot methods with no Bot API counterpart. Options `--json`, `--exclude`, `--strict`, `--format github`; exits with 1 on errors.
- `check_telegram_project` MCP tool with the same check; offered only by the local stdio server because it reads files.
- GitHub Action (`uses: Kay0k1/telegram-dev@v0.9.0`) that runs the check on a repository and annotates the findings.
- The skill checks the whole project after changing or reviewing an existing bot.

### Changed

- The "required unless" warning of `check_bot_api_call` says when it is fine to leave the parameter out.

## [0.8.0] - 2026-11-10

### Added

- `get_bot_api_definition`: one Bot API method or type as structured data — parameters or fields with types, required flags, allowed values, constants and length limits stated by Telegram — plus the changelog entries that mention it.
- `check_bot_api_call`: checks a request payload against the current Bot API schema. Errors for unknown methods and parameters (with close-match suggestions), missing required parameters, wrong types, values outside the documented list and wrong `type` in union objects such as `InputMedia`; warnings for length limits, numbers or booleans sent as strings, "required unless" parameters and parameters retired in an older Bot API version, quoting the changelog entry that replaced them.
- `list_bot_api_changes`: the official Bot API changelog as structured releases, filtered by version or by a method, type or field name.
- `bot_api_schema.py`: builds the schema from the cached official API page and changelog, so it follows new Bot API versions without hand-written definitions.
- `evals/code-tasks.json` and `evals/grade_code.py`: code-writing tasks graded automatically by the requests the answer sends.

### Changed

- The skill uses the structured Bot API tools instead of reading the long API page, checks every Bot API request it writes, and does not repeat a lookup with web search when the server already answered with fresh evidence.

## [0.7.0] - 2026-11-10

### Changed

- MCP tools follow one verb-noun naming scheme. Renamed: `telegram_corpus_status` → `get_telegram_corpus_status`, `telegram_document_history` → `list_telegram_document_revisions`, `telegram_sources` → `list_telegram_sources`. `search_telegram_docs` and `get_telegram_document` are unchanged. The skill uses the new names; update a project install with `uvx telegram-dev@latest install --agent <agent> --update`.
- Every tool description names its neighbouring tools and says when to use them instead.

### Added

- `list_telegram_cached_pages`: pages already stored in the local cache, filtered by area, with freshness and paging.

## [0.6.1] - 2026-11-10

### Changed

- MCP tool definitions: every tool has a short title and a description of when to use it and what it returns; every parameter has a description, examples and limits (`limit` 1–20, `length` 100–40000, `offset` ≥ 0); `area` is a list of allowed values instead of free text.
- `glama.json` pins the Glama build spec (Python 3.14 until dependencies support 3.15).

## [0.6.0] - 2026-11-10

### Added

- `evals/`: 11 Telegram and TON tasks with rubrics checked against the official pages, a Codex CLI runner (`run_codex.py`) for runs with and without Telegram Dev and with and without web access, a grader (`grade.py`), and the first results with transcripts. With Codex's web access the plugin made no difference (45/47 rubric facts both ways); without web access it did (45/47 against 38/47), on the Bot API 10.4 release and the current TON coin and wallet names.
- Bot library documentation: aiogram 3 (`docs.aiogram.dev/en/latest/`: dispatcher, routers, filters, FSM and scenes, middlewares, utils, client session, changelog, migration guide), python-telegram-bot (`docs.python-telegram-bot.org/en/stable/`: `telegram.ext`, `Bot`, `Message`/`Update`/`CallbackQuery`, examples, changelog; and the official wiki) and grammY (`grammy.dev`: guide, advanced, plugins, hosting, read from the site's Markdown sources). About 250 pages; generated per-type pages that mirror the Bot API, grammY's `/ref/` and translations are left out.
- Search areas `aiogram`, `python-telegram-bot` and `grammy`. Core Telegram docs rank first unless the query names a library (`aiogram`, `PTB`, `python-telegram-bot`, `telegram.ext`, `grammY`, with an optional version); the name is not required in the matched text.
- Released aiogram and python-telegram-bot docs (`/en/vX.Y.Z/`) can be read on demand to match the installed version; they are not crawled.
- Skill guide `bot-libraries.md`: find the installed version, read the matching library docs, compare with the Bot API page and changelog, and say when the indexed docs describe another version.
- The daily source monitor covers the four library entry points (61 sources in total).

## [0.5.1] - 2026-11-10

### Fixed

- `uv sync --frozen` on a machine without Python failed: uv picked Python 3.15, for which the locked pydantic-core and rpds-py had no wheels, and anyio does not yet start on 3.15. The project now requires Python `>=3.10,<3.15`, so uv installs 3.14, and the lock uses pydantic-core, rpds-py, anyio and MCP SDK dependencies with current wheels. This fixes Glama builds and the Claude Code plugin on such machines.
- CI also runs the tests on the newest Python the project allows, installed by uv.

## [0.5.0] - 2026-11-10

### Added

- TON documentation: every page listed in the docs.ton.org `llms.txt` index (TON Connect, payments, APIs, smart contracts, Tolk, TVM, blockchain foundations), the TEP standards, the TON node and Tolk changelogs, and Telegram's Blockchain Guidelines for Mini Apps. Pages are read as Markdown and cited by their docs.ton.org URLs.
- Search areas `ton` and `ton-releases`; Russian aliases for wallets, contracts, jettons and NFTs.
- Skill guide `ton-and-blockchain.md`: Telegram's rules first (TON and TON Connect only, Stars for digital goods), then TON Connect and `ton_proof`, payment confirmation, standards, testnet and key safety.
- The daily source monitor covers the new TON sources (57 in total).

## [0.4.0] - 2026-11-10

### Added

- `telegram-dev install --agent claude|codex|cursor` installs the MCP server and the skill into a project with one command: `uvx telegram-dev install --agent claude`. The skill now ships inside the Python package.
- Installs from the package pin the server to the installed version (or exact git commit) through `uvx`, so no checkout has to stay on disk. Installs from a checkout keep using the checkout's Python.
- `--from` overrides the package the server is launched from; `--project` defaults to the current directory and refuses the home directory.
- `telegram-dev --version`; the MCP server reports the package version and project URL.
- `server.json` for the official MCP Registry.
- Release workflow: a tag builds, tests and publishes the GitHub release with the wheel, sdist, source ZIP, skill-only ZIP and checksums. PyPI and MCP Registry publishing are opt-in through repository variables.
- `CHANGELOG.md`.

### Changed

- The Python distribution is named `telegram-dev` (was `telegram-dev-knowledge`).
- `README.md` is in English and starts with a real agent run; the Russian guide is in `README.ru.md`.
- `scripts/install.py` is a thin wrapper around `telegram_dev_install.py` and keeps working for existing checkouts.

## [0.3.0] - 2026-10-10

### Added

- Reference guides for bots, Mini Apps, MTProto/TDLib, calls, Secret Chats, business, payments, groups, channels and media.
- Freshness checks on read and search, a background refresh cycle and a daily public monitor of 52 official sources.
- `--update` for installed skills, refusing to overwrite local edits.
- Custom Codex and Claude Code plugin catalogs, Streamable HTTP transport and a container deployment.

## [0.2.0] - 2026-09-24

### Added

- First public release: documentation MCP server with an on-demand local cache, agent skill, project installer for Codex, Claude Code and Cursor, and a Claude Code plugin catalog.

[0.9.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/Kay0k1/telegram-dev/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/Kay0k1/telegram-dev/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Kay0k1/telegram-dev/releases/tag/v0.2.0
