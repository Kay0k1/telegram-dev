# Проверки / Validation

## 0.4.0 — 2026-11-10 (Linux)

| Check | Result |
| --- | --- |
| Repository tests | **47 passed**: the 41 from 0.3.0 plus package installs (index, git, explicit `--from`), the `install` and `--version` CLI and manifest/`server.json` version consistency |
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
