# Telegram Dev

Telegram development skill + documentation MCP for Codex, Claude Code, and Cursor.

Helps coding agents choose the right Telegram API, look up current documentation, and check the requested behavior. Includes specific guidance for colored buttons, custom/premium emoji, stickers, voice messages, video notes, Mini Apps, Bot API, MTProto and TDLib.

[Русская инструкция](README.ru.md) · [Download releases](https://github.com/Kay0k1/telegram-dev/releases) · [Report an issue](https://github.com/Kay0k1/telegram-dev/issues)

**Experimental.** This is an independent community project, not an official Telegram product. Installing it does not guarantee correct model behavior. Native application activation still needs to be verified after installation.

## Install in your project

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then download this repository or clone it:

```sh
git clone https://github.com/Kay0k1/telegram-dev.git
cd telegram-dev
uv run --frozen python scripts/install.py --agent codex --project /absolute/path/to/your-project
```

Replace `codex` with `claude` or `cursor` for that agent. On Windows use a quoted Windows project path. This command installs dependencies, adds the MCP connection, and copies the skill into your chosen project. Existing unrelated settings are preserved and existing config files are backed up. It refuses to overwrite an existing Telegram Dev connection or skill.

Keep the downloaded repository and its `.venv` in place: the connection points to them. Open a new agent session; enable/trust the project MCP server when your application asks. Codex project settings require a trusted project. Installed paths are machine-specific and should be regenerated for another developer.

## Claude Code plugin catalog

With `uv` on your PATH, run inside Claude Code:

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

This is our repository-backed catalog, not a listing in Anthropic's official curated directory. Choose either plugin installation or the project installer above, not both. Follow the reload/new-session instruction reported by Claude Code. The plugin skill is named `/telegram-dev:telegram-dev`.

## Try it

Ask your agent:

> Use telegram-dev. Check the corpus status, fetch the current Bot API documentation if needed, and find how to make an inline button red and add a custom emoji icon. Read the relevant requirements and cite the source. Do not send any messages.

Check that it actually calls `telegram_corpus_status`, `get_telegram_document`, and `search_telegram_docs`. Then use the skill for normal implementation tasks in your codebase.

## How the knowledge base works

The public package starts with an **empty local cache**. The skill directs the agent to fetch the relevant official entrypoint first; that page is indexed immediately. There is no prerequisite full-site crawl, paid search service or Telegram login.

Documentation is stored in your platform's user cache directory, outside the plugin installation. Set `TELEGRAM_KNOWLEDGE_DB` to override the database path. The public release contains code and skills; it does not bundle the development snapshot of downloaded Telegram documentation.

Optional full indexing and refresh:

```sh
uv run --frozen telegram-dev sync --max-pages 0
uv run --frozen telegram-dev status
uv run --frozen telegram-dev sync --refresh --max-pages 0
```

The crawler follows bounded official documentation links. It reports unavailable pages and does not claim to contain every past Telegram version, private implementation detail or client source file. Retrieved documents remain reference data, not agent instructions. Search is local full-text search with a small set of Russian aliases, not multilingual semantic search.

## MCP tools

| Tool | Purpose |
|---|---|
| `telegram_corpus_status` | Inspect indexed scope, freshness and gaps |
| `get_telegram_document` | Fetch/read a source with pagination and optional refresh |
| `search_telegram_docs` | Find relevant sections, filtered by API area |
| `telegram_document_history` | List revisions observed by this installation |

## Development

```sh
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv build
```

Tests cover search, API boundaries, revisions, pagination, MCP protocol calls and project installation. The evaluation prompts in `tests/behavioral-cases.json` are proposed full-agent tests, not a claim of passed evaluations. CI exercises the package on Linux, macOS and Windows; check the actual workflow results.

Contributions: open an issue with your original request, expected Telegram behavior, actual result, relevant library/client versions, and official source where applicable. Do not include tokens, private sessions or personal chat logs. For code changes, add a focused regression test and open a pull request.

## Distribution status

GitHub source and tagged releases are the distribution route. Claude Code can add the repository as a custom catalog. Cursor and OpenAI marketplace submissions are separate review processes and have not been submitted or approved. The included native manifests are integration metadata; their presence is not a store listing or proof of end-to-end native UI testing.

For Codex, use the project installer for the complete setup; its standalone native manifest exposes the skill only. The Python wheel exposes the MCP/CLI; use the repository or release ZIP for the installer and skill assets.

Publication routes: [Claude Code catalogs](https://code.claude.com/docs/en/plugin-marketplaces), [Cursor plugins](https://cursor.com/docs/plugins), [OpenAI plugin submission](https://developers.openai.com/plugins/deploy/submission).

## License

MIT for original project code and instructions. Retrieved third-party documentation retains its original ownership and terms; see [NOTICE](NOTICE).
