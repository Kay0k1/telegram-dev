# Telegram Dev — notes for coding agents

MCP server + agent skill that give Claude Code, Codex and Cursor current official Telegram and TON documentation. TON pages are crawled from the Markdown twins listed in `https://docs.ton.org/llms.txt` and cited by their human URLs (`fetch_location()` maps between them). Bot library docs (aiogram, python-telegram-bot docs and wiki, grammY) use the same pattern where Markdown exists (grammY site sources, PTB wiki); `library_path()` holds each library's boundary, `LIBRARY_AREAS` the search areas, `INDEX_ONLY` the discovery-only indexes (grammY sitemap, PTB wiki sidebar). `CLAUDE.md` is a symlink to this file.

## Layout

- `telegram_knowledge.py` — the whole server and CLI: crawler, SQLite FTS5 cache, freshness policy, MCP tools (`serve`, `search`, `status`, `sync`, `maintain`; `install` is dispatched to the installer).
- `bot_api_schema.py` — parses the cached Bot API page and changelog Markdown into a schema (methods, types, constraints, releases) and checks request payloads; nothing is hand-written per method. Used by `get_bot_api_definition`, `check_bot_api_call`, `list_bot_api_changes`.
- `telegram_dev_install.py` — project installer. From a checkout it points the agent at the checkout's Python; from the package it writes a pinned `uvx --from <spec> telegram-dev serve` launcher (spec detected from `direct_url.json`).
- `skills/telegram-dev/` — the skill; shipped in the wheel as the `telegram_dev_skill` package (see `[tool.setuptools]` in `pyproject.toml`).
- `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.agents/plugins/` — native plugin manifests and catalogs. `server.json` — MCP Registry entry.
- `scripts/check_sources.py` — daily source monitor (`.github/workflows/documentation.yml`, results on the `docs-status` branch). `scripts/package_openai.py` — OpenAI submission ZIPs.
- `docs/` — runtime settings, deployment, validation record, catalog submission steps.

## Rules

- Run `uv run --frozen python -m unittest discover -s tests -v` before committing. Add a regression test for logic changes.
- A release bumps the version in `pyproject.toml`, all plugin manifests, `server.json` and `CHANGELOG.md` together (`VersionTests` enforces it), then `uv lock`. Tag `vX.Y.Z` triggers `.github/workflows/release.yml`.
- `README.md` is English, `README.ru.md` Russian; keep them in sync. Keep the `mcp-name:` comment in `README.md`.
- Library docs stay bounded: guides and bot-facing references only. Do not add generated per-type pages that mirror the Bot API (aiogram `api/types`, `api/methods`; PTB `telegram.<Type>`; grammY `/ref/`); core.telegram.org covers them. Pinned versions (`/en/vX.Y.Z/`) are read on demand and never added to the frontier.
- The server only reads public documentation. Never add Telegram account access, message sending or bundled copies of Telegram docs.
- Conventional commits.
