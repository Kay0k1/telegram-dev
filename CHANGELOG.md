# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-11-10

### Added

- `telegram-dev install --agent claude|codex|cursor` installs the MCP server and the skill into a project with one command: `uvx telegram-dev install --agent claude`. The skill now ships inside the Python package.
- Installs from the package pin the server to the installed version through `uvx`, so no checkout has to stay on disk. Installs from a checkout keep using the checkout's Python.
- `--from` overrides the package the server is launched from; `--project` defaults to the current directory.
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

[0.4.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Kay0k1/telegram-dev/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Kay0k1/telegram-dev/releases/tag/v0.2.0
