# Проверки / Validation

## 0.8.0 — 2026-11-10 (Linux)

Bot API schema, call checks and changelog tools, checked against the live Bot API 10.4 page and changelog cached on 2026-11-10.

| Check | Result |
| --- | --- |
| Parsing | 193 methods and 425 types; every type name referenced by a parameter or field resolves; 29 union types; 17 enum fields, 184 constant fields (`type`, `status`, `source` discriminators and one currency), 135 length limits, 14 "required unless" parameters |
| Independent cross-check | aiogram 3.31.0 (Bot API 10.3, generated from the same page): all 185 of its methods are in the schema; every parameter it has that the schema lacks is explained by the changelog (ephemeral parameters moved into `ephemeral_message_parameters` in 10.4, `reply_to_message_id`, `disable_web_page_preview`, `correct_option_id`, `switch_pm_*` and others replaced earlier) |
| Retired parameters | All 69 parameters aiogram still accepts but the current docs no longer list are reported as warnings naming the Bot API version and changelog entry that replaced them, not as errors |
| False positives | A minimal valid payload built from the schema for each of the 193 methods passes with no errors (14 send methods keep the expected warning that `chat_id` is required unless the message is an ephemeral reply) |
| Detection | 502 broken payloads (each required parameter removed in turn, plus an invented parameter per method): all 502 rejected |
| MCP | With an empty cache the server fetched the page and changelog and answered `get_bot_api_definition("InlineKeyboardButton")` (14 fields, 6 changelog entries, about 6,400 characters) in 3.5 s; later checks take about 10 ms |
| Tests | 84 repository tests, including 10 for the schema on a hand-written page excerpt |

## 0.6.0: agent evals — 2026-11-10 (Linux)

Does the plugin change what an agent answers? 11 Telegram and TON tasks with rubrics checked against the official pages, run with Codex CLI 0.167.0 (`gpt-6.1-sol`, effort `ultra`) and telegram-dev 0.5.0 from PyPI, each in a fresh project, in four configurations. Details, per-task results, transcripts and limitations: [evals/README.md](../evals/README.md).

| Configuration | Rubric facts | Tasks fully correct | Wrong claims |
| --- | --- | --- | --- |
| Telegram Dev + Codex web access | 45/47 | 9/11 | 0 |
| Codex web access only | 45/47 | 9/11 | 0 |
| Telegram Dev, web access off | 45/47 | 9/11 | 0 |
| Neither | 38/47 | 8/11 | 1 |

- With web access, Codex read core.telegram.org and docs.ton.org itself and matched the plugin on every task.
- With web access off, only the plugin runs knew Bot API 10.4 (HTML widgets) and the current TON names (Gram, Telegram Money, WalletTg); a second run of these tasks gave the same split. The run without the plugin named the old ones (Toncoin, Wallet in Telegram, Wallet V5).
- On the Tolk task the plugin runs scored one fact lower: they did not mention FunC, which the run without the plugin called Tolk's predecessor.
- Not measured: Claude Code (headless login expired on the test machine), Cursor, other models, executing the generated code.

## 0.6.0: bot library docs — 2026-11-10 (Linux)

| Check | Result |
| --- | --- |
| Repository tests | **72 passed** with the evals from main, including 15 new library tests: URL boundaries per host (no query strings, assets, `_modules`/`_static`, generated type and method pages, `/ref/`, translations, other repositories), the `telegram.ext.` prefix not matching `telegram.externalreplyinfo`, Markdown twins for grammY and the PTB wiki, the grammY sitemap and PTB wiki sidebar feeding discovery without search chunks, pinned versions read but never queued, Sphinx anchor and `[source]` cleanup, and ranking |
| Library crawl | Real crawl into a temporary `TELEGRAM_KNOWLEDGE_DB` from the four library entry points plus seven core bot pages, following library links only: 58 s, **aiogram 55 pages** (3.31.0, `latest`; 0.71 M characters), **python-telegram-bot 128** (85 pages of v22.8 `stable` docs and 43 wiki pages; 3.90 M characters, of which the `Bot` class page is 1.6 M), **grammY 69** (68 pages and the sitemap index; 0.65 M characters). 2,838 search chunks in total; no pinned-version pages entered the crawl. Compared with each Sphinx site's `searchindex.js`, every in-scope aiogram (55/55) and PTB (85/85) page was reached |
| Library errors | Three PTB wiki links return 404 on GitHub itself (`Bot-API-Backward-Compatibility`, `Types-Of-Handlers` — the page is `Types-of-Handlers`, `location_keyboard,-contact_keyboard`) |
| Source monitor | `scripts/check_sources.py` fetched the four new entry points: aiogram, PTB, the PTB wiki sidebar and the grammY sitemap (61 sources in total) |

Search over that database (top result per query; core pages are the Bot API, features, FAQ, inline, Stars payments, changelog and Mini Apps):

| Query | First results |
| --- | --- |
| `aiogram 3 callback query handler` | aiogram `dispatcher/router.html` § Callback query, `utils/callback_answer.html`, `dispatcher/filters/callback_data.html` |
| `PTB ConversationHandler` | PTB `telegram.ext.conversationhandler.html`, then the wiki's v20 transition guide |
| `grammY inline keyboard` | grammY `plugins/keyboard` § Sending an Inline Keyboard, § Building an Inline Keyboard, § Responding to Inline Keyboard Clicks |
| `python-telegram-bot JobQueue run_repeating` | PTB `telegram.ext.jobqueue.html`, wiki `Extensions---JobQueue` |
| `grammY conversations plugin` | grammY `plugins/conversations` |
| `inline keyboard` (no library named) | Only Bot API sections (`InlineKeyboardMarkup`, the send methods' `reply_markup`) in the top five |
| `answerCallbackQuery`, `webhook` | Only Bot API and Bot FAQ pages in the top five |
| `sendMessage reply_markup` | Bot API `sendMessage` first; library keyboard pages after the core matches |

Not verified: an agent run that uses the library docs on a real project; a full background refresh cycle with the complete core corpus (61 seeds now exceed half of the default 120-page budget, so the default cycle uses the round-robin path that small budgets already used).

## 0.5.0 — 2026-11-10 (Linux)

| Check | Result |
| --- | --- |
| Repository tests | **55 passed**, including TON URL boundaries, Markdown fetching via the `llms.txt` twins, TEP link resolution and the `ton` / `ton-releases` areas |
| TON crawl | Starting from the TON sources, 463 TON pages and 3 TON release pages were indexed. Three TON links failed because docs.ton.org itself returns 404 (`/languages/fift`, `/tvm`) or redirects off-site (`/contracts/acton`) |
| TON search | Exact hits for TON Connect transactions, jetton transfers, Gram, Tolk structs, `ton_proof`, WalletTg and the Russian query «кошелек»; Telegram's Blockchain Guidelines rank next to TON Connect |
| Source monitor | `scripts/check_sources.py` fetched all five new TON sources |
| Real agent run | Codex CLI 0.167.0 with the 0.5.0 wheel installed: asked to sell a Mini App skin for 2 TON, it read the Stars and TON Connect pages over MCP and answered that digital goods must use Stars (`XTR`), with TON Connect only for permitted wallet features. This run is the second README example |

## 0.4.0 — 2026-11-10 (Linux)

| Check | Result |
| --- | --- |
| Repository tests | **49 passed**: the 41 from 0.3.0 plus package installs (index, git commit pinning, explicit `--from`, refusal of credential URLs and the home directory), the `install` and `--version` CLI and manifest/`server.json` version consistency |
| Build | `uv build` produced `telegram_dev-0.4.0` wheel and sdist; the wheel contains `telegram_knowledge`, `telegram_dev_install` and the skill with all references |
| One-command install | `uvx --from <wheel> telegram-dev install --agent claude` and `--agent codex` in empty projects: skill copied, MCP entry written as a pinned `uvx` launcher |
| Migration | A checkout install (0.3.0 style, absolute Python path) updated with the package and `--update`: the connection moved to `uvx`, other settings kept |
| MCP over stdio | The installed `.mcp.json` entry, started by the official MCP Python client: 5 tools listed, Bot API page fetched (681,414 characters), search found `InlineKeyboardButton` |
| Real agent run | Codex CLI 0.167.0 in a fresh trusted project: the agent read the skill, made 10 MCP calls (`telegram_corpus_status`, `search_telegram_docs`, `get_telegram_document` on the Bot API and its changelog) and answered with `style: "danger"`, `icon_custom_emoji_id`, the eligibility rules and links. This run is the README example |
| `server.json` | Valid against `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` |
| Release workflow | Schema-checked; its build, archive, notes and wheel-install steps were run locally. The workflow itself runs on the first tag push |

Not verified yet: installing from PyPI (`uvx telegram-dev`) before the package is published; Claude Code and Cursor running the installed server in their apps (Claude Code headless was not available in this environment); the Cursor install button; MCP Registry publishing. Codex reads `.codex/config.toml` only when the exact project directory is trusted: trust in a parent directory did not apply to a nested repository.

## 0.3.0

### Русский

Проверено **2026-10-10** на Linux. Ниже разделены проверки кода, установки и поведения агента: успешная сборка не доказывает, что каждый сценарий выполнен в Telegram.

| Проверка | Наблюдаемый результат |
| --- | --- |
| Автоматические тесты репозитория | **41 тест прошли** после последних исправлений: получение и извлечение страниц, маршрутизация API, поиск, версии и пагинация, обновление/ошибки/фоновые обходы, MCP, установщик, монитор источников и упаковка |
| Проверки ZIP внутри этого набора | **6 тестов**: независимый skills-only пакет, условные требования remote MCP, сохранность полей, ссылки/иконки, отклонение заглушек и защита существующего файла; README проверяется на порядок русский → English |
| Структура скилла | `quick_validate.py` из skill-creator: `Skill is valid!` |
| Python-пакеты | `uv build` создал source distribution и wheel версии **0.3.0** |
| Содержимое source distribution | Включены нативные манифесты/каталоги, `.mcp.json`, иконки, инструкции и справочники скилла, документация и установщик; не обнаружены окружения, кеши, базы данных, session-файлы и секретные конфиги |
| Нативная установка Codex | CLI **0.162.1**: собственный marketplace, установка и `plugin/read` прошли в отдельной временной конфигурации. У полного локального плагина загружены один скилл и пять MCP-инструментов из установленного кеша; относительный `cwd` работает |
| Нативная установка skills-only | Пробный ZIP установлен тем же механизмом: один скилл, **ноль MCP-серверов** |

Wheel содержит MCP/CLI, а не полный установочный плагин: для скилла и нативных каталогов используйте репозиторий или исходный архив. Состав окончательных release-файлов нужно проверить после их сборки из опубликованной версии. Нативные проверки не копировали авторизацию, не вызывали модель и не проверяли интерфейс Codex desktop. Валидация Claude CLI **2.1.296** в строгом режиме также приняла манифест плагина и marketplace; это проверка схемы, не запуск приложения.

#### Независимая проверка четырёх задач

Отдельный агент прочитал скилл, получил публичные официальные источники и подготовил код/планы для четырёх заданий: красная inline-кнопка с custom emoji; Telegram Login для обычного сайта; звонки и Secret Chats через TDLib; business stories и темы в приватных чатах. Выполнено **11 отдельных offline-проверок** построенных запросов и серверных проверок OIDC. Это дополнительный прогон, не часть 41 тест репозитория и не общий рейтинг качества модели.

Проверка выявила три воспроизводимые ошибки получения документации. После исправлений и повторного чтения наблюдались полный текст Secret Chats вместо одного введения, результаты Telegram Login в области web integrations и чтение официальной TDLib-схемы по закреплённому commit SHA. Для этих ошибок добавлены три регрессионных теста в [test_fetch.py](../tests/test_fetch.py). Актуальность загрузки TDLib changelog не трактовалась как доказательство актуальной версии установленной библиотеки.

Дополнительная проверка обновлений обнаружила повторную обработку первых источников при малом бюджете и пропуск новых результатов после обновления поискового совпадения. Исправления проверены тремя регрессионными тестами в [test_refresh.py](../tests/test_refresh.py): продвижение обхода при бюджете в одну страницу, обновление вновь появившихся результатов и сохранение предела в шесть уникальных источников за поиск.

Дополнительные регрессии проверяют продвижение обхода с бюджетом в одну страницу, повторное обновление изменившейся поисковой выдачи и предел в шесть источников, остановку очереди загрузок, перенос прежнего API-семейства при неизменном тексте и завершение возобновлённого обхода по свежему кешу или при backoff ошибки.

Токены бота, Telegram login codes и session-файлы не использовались. Реальные отправки, вид кнопки в клиентах, вход через Telegram, публикация stories, включение приватных тем и двусторонний звук не проверялись. Они требуют конкретного проекта, подходящих прав и отдельно разрешённого действия. [behavioral-cases.json](../tests/behavioral-cases.json) содержит задания для будущих прогонов: наличие этих сценариев не означает, что все они пройдены.

#### Повторить проверки

Из корня проекта:

```sh
uv run --frozen python -m unittest discover -s tests -v
uv build
```

Для проверки скилла, если установлен OpenAI skill-creator, укажите фактический путь к его `scripts/quick_validate.py`. Его дополнительная зависимость PyYAML запускается во временном окружении и не меняет lock проекта:

```sh
uv run --no-project --with PyYAML python /path/to/skill-creator/scripts/quick_validate.py /absolute/path/to/telegram-dev/skills/telegram-dev
```

Проверки кабинета OpenAI, подпись издателя, review и публикация идут отдельно. Здесь нет подтверждения официальной подачи или одобрения; порядок действий описан в [catalog-submissions.md](catalog-submissions.md).

### English

Verified on Linux on **2026-10-10**: **41 repository tests**, including **six archive tests**, passed after the final fixes. The skill-creator structure validator passed; `uv build` produced the **0.3.0** source distribution and runtime-only wheel. The source archive includes native manifests/catalogs, icons, skill resources, documentation and installer files without environments, caches, databases, session files or secret configuration. Inspect the final release artifacts again after building them from the published revision.

Codex CLI **0.162.1** installed the full local plugin through an isolated custom marketplace and exposed one skill plus all five MCP tools from the installed cache. Relative `cwd` launch worked. An independent skills-only archive exposed one skill and no MCP servers. No authentication was copied, no model calls were made and the desktop UI was not tested. Claude CLI **2.1.296** accepted both manifests under strict validation; this establishes schema compatibility, not application runtime behavior.

An independent agent followed four developer requests using current public official sources and produced request builders/plans for colored buttons/custom emoji, website Telegram Login, TDLib calls/Secret Chats, and business stories/private topics. **11 additional offline checks** passed. Three discovered retrieval defects were fixed, directly rechecked and covered by regression tests: truncated Secret Chats extraction, incorrect Login search routing and revision-pinned official TDLib reads.

Further refresh regression tests verify progress with a one-page background budget, refresh of newly exposed search matches and the six-source refresh limit when results reorder, cancellation of queued fetches, unchanged-content API-family migration, and completion of resumed sync during cache hits or failure backoff.

No Telegram tokens, login codes, sessions or live account actions were used. Actual client appearance, sign-in, story publication, private-topic activation and bidirectional audio remain unverified. The behavioral scenario inventory is not a claim that every scenario passed. Portal scans, publisher verification, official review and publication remain separate from these checks; see the [submission workflow](catalog-submissions.md).
