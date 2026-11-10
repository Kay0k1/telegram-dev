# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `evals/`: 11 Telegram and TON tasks with rubrics checked against the official pages, a Codex CLI runner (`run_codex.py`) for runs with and without Telegram Dev and with and without web access, a grader (`grade.py`), and the first results with transcripts. With Codex's web access the plugin made no difference (45/47 rubric facts both ways); without web access it did (45/47 against 38/47), on the Bot API 10.4 release and the current TON coin and wallet names.

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

[0.5.1]: https://github.com/Kay0k1/telegram-dev/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Kay0k1/telegram-dev/releases/tag/v0.2.0
