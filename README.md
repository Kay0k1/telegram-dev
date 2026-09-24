# Telegram Dev

[![Tests](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/Kay0k1/telegram-dev?include_prereleases)](https://github.com/Kay0k1/telegram-dev/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[Русский](#russian) · [English](#english)**

<a id="russian"></a>
## Русский

**Дайте своему AI-агенту документацию Telegram и правила, как по ней разрабатывать.**

Telegram Dev — открытый скилл и MCP-сервер для **Codex, Claude Code и Cursor**. Он помогает агенту выбрать подходящий API, проверить актуальные возможности Telegram и реализовать именно то поведение, которое вы попросили.

«Сделай красную кнопку», «добавь premium emoji», «отправляй видео кружком» — такие задачи требуют проверки конкретного API, формата и ограничений. Telegram Dev задаёт агенту этот порядок работы и даёт инструменты для поиска официальных источников.

[Скачать релиз](https://github.com/Kay0k1/telegram-dev/releases) · [Сообщить об ошибке](https://github.com/Kay0k1/telegram-dev/issues) · [Инструкции скилла](skills/telegram-dev/SKILL.md)

> **Статус: public preview.** Независимый проект сообщества. Документация загружается по запросу; качество ответа зависит и от агента. Проект не связан с Telegram и не является его официальным продуктом.

**Навигация:** [Установка](#ru-install) · [Примеры](#ru-examples) · [Возможности](#ru-scope) · [Как работает](#ru-how) · [Проблемы](#ru-help) · [Разработка](#ru-dev)

<a id="ru-install"></a>
### Быстрый старт

Понадобятся [uv](https://docs.astral.sh/uv/getting-started/installation/) и папка проекта, в котором вы работаете с агентом. Для получения публичной документации **не нужны токен бота, Telegram-аккаунт или платный сервис поиска**. Для первой загрузки страниц нужен интернет.

**1. Скачайте Telegram Dev.** Клонируйте репозиторий или распакуйте ZIP со [страницы релизов](https://github.com/Kay0k1/telegram-dev/releases).

```sh
git clone https://github.com/Kay0k1/telegram-dev.git
cd telegram-dev
```

**2. Выполните одну команду для своего агента.** Замените путь в кавычках на полный путь к существующему рабочему проекту. Команду запускайте из папки Telegram Dev.

| Агент | Значение `--agent` | Что устанавливается в рабочий проект |
| --- | --- | --- |
| Codex | `codex` | MCP в `.codex/config.toml`, скилл в `.agents/skills/telegram-dev` |
| Claude Code | `claude` | MCP в `.mcp.json`, скилл в `.claude/skills/telegram-dev` |
| Cursor | `cursor` | MCP в `.cursor/mcp.json`, скилл в `.cursor/skills/telegram-dev` |

```sh
# Codex
uv run --frozen python scripts/install.py --agent codex --project "/absolute/path/to/your-project"

# Claude Code
uv run --frozen python scripts/install.py --agent claude --project "/absolute/path/to/your-project"

# Cursor
uv run --frozen python scripts/install.py --agent cursor --project "/absolute/path/to/your-project"
```

На Windows путь выглядит, например, так: `--project "C:\Users\you\Projects\my-bot"`.

Установщик подключает MCP и копирует скилл. Посторонние настройки сохраняются, для существующего файла конфигурации создаётся резервная копия. Повторная установка поверх существующего подключения или скилла останавливается с объяснением.

**3. Откройте новую сессию агента.** Разрешите подключение проектного MCP, если приложение запросит это. В Codex проект должен быть доверенным. Оставьте папку Telegram Dev и её `.venv` на месте: подключение использует абсолютные пути к ним. На другой машине установщик нужно запустить заново.

**4. Дайте первое задание.** Например:

> Используй telegram-dev. Проверь состояние базы, загрузи актуальную документацию Bot API и найди, как сделать красную inline-кнопку с custom emoji. Прочитай требования и покажи ссылки на источники. Пока ничего не отправляй в Telegram.

При первом запуске база пустая — это ожидаемо. Агент должен проверить `telegram_corpus_status`, получить страницу через `get_telegram_document` и найти нужные разделы через `search_telegram_docs`.

#### Альтернатива: каталог Claude Code

Если `uv` доступен приложению, выполните внутри Claude Code:

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

Затем выполните предложенную приложением перезагрузку или откройте новую сессию. Имя скилла в плагине — `/telegram-dev:telegram-dev`.

Это собственный каталог проекта на GitHub. Выберите каталог **или** установщик выше, чтобы не создавать два подключения.

<a id="ru-examples"></a>
### Что попросить у агента

Примеры можно копировать и адаптировать к своему проекту.

**Кнопки и custom emoji**

> Используй telegram-dev. В существующем боте сделай кнопку «Удалить» красной и добавь custom emoji. Проверь текущий Bot API, ограничения для этого бота и поддержку полей нашей библиотекой. Внеси изменения в код и укажи, что проверено локально, а что нужно проверить в Telegram.

**Голосовые и кружки**

> Используй telegram-dev. Этот ролик должен отправляться как кружок. Проверь метод API и требования к файлу, доработай подготовку и отправку. Сохрани существующий стек проекта.

**Mini Apps**

> Используй telegram-dev. Проверь авторизацию нашей Mini App: как сервер проверяет initData, срок его действия и ошибки. Исправь найденные проблемы по официальной документации.

**Обновления Telegram**

> Используй telegram-dev. Найди официальные изменения Bot API, которые затрагивают клавиатуры и эмодзи. Сопоставь их с установленной версией нашей библиотеки и объясни, какие изменения нужны в проекте. Приведи источники и версии.

<a id="ru-scope"></a>
### Какие темы охватывает

Скилл содержит карту официальных источников и проверки для разных направлений разработки:

| Направление | Что агент должен учитывать |
| --- | --- |
| **Боты и Bot API** | Сообщения, клавиатуры, обновления, файлы, права и контекст чата |
| **Форматирование и эмодзи** | Entities, экранирование, UTF-16 offsets, custom emoji и условия использования |
| **Стикеры и медиа** | Форматы ресурсов, наборы стикеров, голосовые, видео и кружки |
| **Mini Apps** | JS bridge, контекст запуска, тема, серверная проверка авторизации |
| **Telegram API / MTProto / TDLib** | Разработка клиентов, методы и типы, различия авторизации бота и пользователя |
| **Другие интеграции** | Deep links, widgets, Gateway, Passport, Instant View и темы |
| **Релизы** | Bot API changelog, API layers, TDLib changelog и официальные анонсы |

Полная карта: [API и источники](skills/telegram-dev/references/surface-map.md). Практические проверки: [по функциям](skills/telegram-dev/references/feature-checks.md) и [по кнопкам и эмодзи](skills/telegram-dev/references/buttons-and-custom-emoji.md).

<a id="ru-how"></a>
### Как это работает

```text
Ваше задание → скилл выбирает API и порядок проверки
            → MCP получает и ищет официальную документацию
            → агент вносит изменения в ваш проект и проверяет результат
```

**Скилл** объясняет агенту, как уточнять ожидаемое поведение, выбирать API, учитывать версии библиотек и проверять результат. **MCP-сервер** предоставляет доступ к документам. **Локальный кеш** сохраняет полученные страницы для повторного поиска.

| MCP-инструмент | Назначение |
| --- | --- |
| `telegram_corpus_status` | Проверить объём базы, свежесть и пробелы |
| `get_telegram_document` | Загрузить или прочитать документ по частям; `refresh=true` обновляет страницу |
| `search_telegram_docs` | Найти разделы документации с фильтром по области API |
| `telegram_document_history` | Посмотреть версии страницы, сохранённые этой установкой |

Публичный пакет содержит код и скилл; готовая копия всей документации в него не включена. Нужные страницы загружаются по запросу и сразу индексируются. Кеш хранится в пользовательском каталоге кеша вашей ОС, отдельно от папки плагина. Свой путь к базе можно задать через `TELEGRAM_KNOWLEDGE_DB`.

Для предварительного сбора всех обнаруженных страниц и последующего обновления выполните из папки Telegram Dev:

```sh
# Собрать доступные страницы в пределах настроенных официальных источников
uv run --frozen telegram-dev sync --max-pages 0

# Проверить состояние базы
uv run --frozen telegram-dev status

# Обновить документы
uv run --frozen telegram-dev sync --refresh --max-pages 0
```

Полный обход может занять время. Он сообщает о недоступных страницах; предварительно запускать его для обычной задачи не требуется.

#### Границы возможностей

- Поиск — локальный полнотекстовый, с небольшим набором русских поисковых соответствий. Точные имена методов и английские термины обычно полезнее свободного пересказа.
- История документа — версии, которые успела сохранить ваша установка. Историю релизов агент проверяет отдельно по официальным changelog и анонсам.
- MCP работает с публичными документами. Доступ к чатам и аккаунту, отправка сообщений и выполнение действий в Telegram требуют отдельных инструментов и разрешений.
- Проект не содержит закрытых знаний Telegram, всех исходников клиентов или гарантированно полной истории платформы. Скилл помогает проверять факты, но не гарантирует безошибочную работу модели.

<a id="ru-help"></a>
### Если что-то не работает

| Симптом | Что проверить |
| --- | --- |
| Агент не видит инструменты | Откройте новую сессию, проверьте включение MCP и доверие к проекту; папка Telegram Dev и `.venv` должны оставаться на месте |
| Поиск ничего не находит | Сначала загрузите нужную страницу через `get_telegram_document`, затем ищите по имени метода или английскому термину |
| Агент ссылается на старые ограничения | Попросите обновить источник с `refresh=true` и проверить версию установленной библиотеки |
| Установщик сообщает `already configured` или `Skill already exists` | Проверьте существующее подключение и скилл: установщик намеренно не перезаписывает их |
| Нужно обновить скопированный скилл | Обновите исходный репозиторий и перенесите изменения из `skills/telegram-dev` в папку скилла проекта, сохранив свои правки; `git pull` сам копию не обновляет |

Если проблема осталась, [создайте issue](https://github.com/Kay0k1/telegram-dev/issues): укажите агент, ОС, версии библиотек, исходное задание, ожидаемый результат и фактическое поведение. Не прикладывайте токены, файлы сессий и личную переписку.

<a id="ru-dev"></a>
### Разработка и вклад в проект

```sh
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv build
```

Тесты проверяют поиск, разделение API, версии документов, чтение по частям, вызовы MCP и установщик. [CI](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml) запускает проверки и сборку на Linux, macOS и Windows.

В [tests/behavioral-cases.json](tests/behavioral-cases.json) лежат сценарии для проверки поведения агента. Это заготовки для таких проверок, а не заявление, что все агенты успешно их прошли. Включение плагина в интерфейсе каждого приложения также требует проверки после установки.

Полезный вклад: воспроизводимые ошибки, новые сценарии, улучшения карты источников, проверок и установки. Откройте issue или pull request; для изменения логики добавьте целевой регрессионный тест.

### Распространение и лицензия

Исходники и ZIP доступны на GitHub. Для Claude Code есть собственный каталог. Заявки в официальные каталоги Cursor и OpenAI пока не поданы. Наличие манифестов в репозитории не означает публикацию в этих магазинах.

Для полного подключения в Codex используйте установщик: отдельный нативный манифест Codex предоставляет только скилл. Python wheel содержит MCP/CLI; установщик и ресурсы скилла берите из репозитория или ZIP релиза. Другие агенты могут подключать сервер при поддержке MCP через stdio, но готовых установщиков для них пока нет.

[MIT](LICENSE) распространяется на оригинальный код и инструкции проекта. Загруженная документация сохраняет права и условия её владельцев — см. [NOTICE](NOTICE).

---

<a id="english"></a>
## English

**Give your AI agent Telegram documentation and a workflow for building with it.**

Telegram Dev is an open-source skill and MCP server for **Codex, Claude Code, and Cursor**. It helps agents select the appropriate API, check Telegram's current capabilities, and implement the behavior you requested.

“Make the button red,” “add a premium emoji,” and “send this video as a video note” require checking specific APIs, formats, and restrictions. Telegram Dev gives the agent a workflow and tools to look up official sources before implementing the feature.

[Download a release](https://github.com/Kay0k1/telegram-dev/releases) · [Report an issue](https://github.com/Kay0k1/telegram-dev/issues) · [Read the skill](skills/telegram-dev/SKILL.md)

> **Status: public preview.** An independent community project. Documentation is fetched on demand; answer quality also depends on the agent. This project is not affiliated with Telegram or an official Telegram product.

**Contents:** [Install](#en-install) · [Examples](#en-examples) · [Coverage](#en-scope) · [How it works](#en-how) · [Troubleshooting](#en-help) · [Development](#en-dev)

<a id="en-install"></a>
### Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and an existing project directory where you work with your agent. Fetching public documentation requires **no bot token, Telegram account, or paid search service**. An internet connection is needed to fetch pages initially.

**1. Download Telegram Dev.** Clone this repository or extract a ZIP from [releases](https://github.com/Kay0k1/telegram-dev/releases).

```sh
git clone https://github.com/Kay0k1/telegram-dev.git
cd telegram-dev
```

**2. Run one command for your agent.** Replace the quoted path with the absolute path to your existing project. Run the command from the Telegram Dev directory.

| Agent | `--agent` value | Files installed in your project |
| --- | --- | --- |
| Codex | `codex` | MCP in `.codex/config.toml`, skill in `.agents/skills/telegram-dev` |
| Claude Code | `claude` | MCP in `.mcp.json`, skill in `.claude/skills/telegram-dev` |
| Cursor | `cursor` | MCP in `.cursor/mcp.json`, skill in `.cursor/skills/telegram-dev` |

```sh
# Codex
uv run --frozen python scripts/install.py --agent codex --project "/absolute/path/to/your-project"

# Claude Code
uv run --frozen python scripts/install.py --agent claude --project "/absolute/path/to/your-project"

# Cursor
uv run --frozen python scripts/install.py --agent cursor --project "/absolute/path/to/your-project"
```

On Windows, use a path such as `--project "C:\Users\you\Projects\my-bot"`.

The installer connects the MCP server and copies the skill. It preserves unrelated settings and backs up existing configuration files. It refuses to overwrite an existing Telegram Dev connection or skill and explains the conflict.

**3. Open a new agent session.** Enable/trust the project MCP connection if prompted. Codex requires a trusted project. Keep the Telegram Dev directory and its `.venv` in place: the connection uses absolute paths to them. Run the installer again on another machine.

**4. Try your first task.** For example:

> Use telegram-dev. Check the corpus status, fetch the current Bot API documentation, and find how to make an inline button red and add a custom emoji. Read the requirements and cite the sources. Do not send anything to Telegram yet.

An empty database on first launch is expected. The agent should call `telegram_corpus_status`, fetch a page with `get_telegram_document`, and find relevant sections with `search_telegram_docs`.

#### Alternative: Claude Code catalog

With `uv` available to the application, run inside Claude Code:

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

Follow the application's reload instruction or open a new session. The plugin skill is named `/telegram-dev:telegram-dev`.

This is the project's own GitHub-backed catalog. Choose the catalog **or** the installer above to avoid duplicate connections.

<a id="en-examples"></a>
### Example tasks

Copy and adapt these prompts to your project.

**Buttons and custom emoji**

> Use telegram-dev. Make the “Delete” button in our existing bot red and add a custom emoji. Check the current Bot API, this bot's eligibility, and field support in our installed library. Implement the change and distinguish local checks from checks that need Telegram.

**Voice messages and video notes**

> Use telegram-dev. This clip should be sent as a video note. Check the API method and file requirements, then update media preparation and sending. Keep the project's existing stack.

**Mini Apps**

> Use telegram-dev. Review our Mini App authentication: server-side initData validation, expiration, and error handling. Fix the issues using official documentation.

**Telegram updates**

> Use telegram-dev. Find official Bot API changes affecting keyboards and emoji. Compare them with our installed library version and explain the changes our project needs. Include sources and versions.

<a id="en-scope"></a>
### Coverage

The skill includes an official source map and checks for multiple areas of Telegram development:

| Area | What the agent should check |
| --- | --- |
| **Bots and Bot API** | Messages, keyboards, updates, files, permissions, and chat context |
| **Formatting and emoji** | Entities, escaping, UTF-16 offsets, custom emoji, and eligibility |
| **Stickers and media** | Asset formats, sticker sets, voice messages, videos, and video notes |
| **Mini Apps** | JS bridge, launch context, themes, and server-side authentication validation |
| **Telegram API / MTProto / TDLib** | Client development, methods and types, bot versus user authorization |
| **Other integrations** | Deep links, widgets, Gateway, Passport, Instant View, and themes |
| **Releases** | Bot API changelog, API layers, TDLib changelog, and official announcements |

See the [API and source map](skills/telegram-dev/references/surface-map.md), [feature checks](skills/telegram-dev/references/feature-checks.md), and [button and emoji guidance](skills/telegram-dev/references/buttons-and-custom-emoji.md).

<a id="en-how"></a>
### How it works

```text
Your task → the skill guides API selection and verification
          → MCP fetches and searches official documentation
          → the agent changes your project and checks the result
```

The **skill** guides the agent through intended behavior, API selection, library versions, and verification. The **MCP server** provides document access. A **local cache** stores fetched pages for subsequent searches.

| MCP tool | Purpose |
| --- | --- |
| `telegram_corpus_status` | Inspect indexed scope, freshness, and gaps |
| `get_telegram_document` | Fetch or read a source with pagination; `refresh=true` updates the page |
| `search_telegram_docs` | Find documentation sections, filtered by API area |
| `telegram_document_history` | List page revisions captured by this installation |

The public package contains code and the skill; it does not bundle a full documentation snapshot. Pages are fetched on demand and indexed immediately. The cache lives in your platform's user cache directory, outside the plugin directory. Set `TELEGRAM_KNOWLEDGE_DB` to override the database path.

To pre-index all discovered pages and refresh them later, run from the Telegram Dev directory:

```sh
# Fetch available pages within the configured official sources
uv run --frozen telegram-dev sync --max-pages 0

# Inspect corpus status
uv run --frozen telegram-dev status

# Refresh documents
uv run --frozen telegram-dev sync --refresh --max-pages 0
```

A full crawl can take time. It reports unavailable pages; running it first is not required for ordinary tasks.

#### Limitations

- Search is local full-text search with a small set of Russian aliases. Exact method names and English terms are usually more useful than broad paraphrases.
- Document history consists of revisions captured by your installation. The agent checks release history separately in official changelogs and announcements.
- The MCP server handles public documents. Account/chat access, sending messages, and other Telegram actions require separate tools and authorization.
- The project does not contain private Telegram knowledge, every client source file, or a guaranteed complete platform history. The skill supports verification but cannot guarantee correct model behavior.

<a id="en-help"></a>
### Troubleshooting

| Symptom | What to check |
| --- | --- |
| The agent cannot see the tools | Open a new session, check MCP activation and project trust, and confirm the Telegram Dev directory and `.venv` are still in place |
| Search returns nothing | Fetch the relevant page with `get_telegram_document` first, then search by method name or English keyword |
| The agent cites outdated restrictions | Ask it to refresh the source with `refresh=true` and check the installed library version |
| The installer reports `already configured` or `Skill already exists` | Inspect the existing connection and skill; the installer deliberately refuses to overwrite them |
| You need to update the copied skill | Update the source repository and transfer changes from `skills/telegram-dev` into the project's skill directory, preserving your edits; `git pull` does not update that copy automatically |

Still stuck? [Open an issue](https://github.com/Kay0k1/telegram-dev/issues) with your agent, OS, library versions, original request, expected result, and actual behavior. Do not include tokens, session files, or personal chat logs.

<a id="en-dev"></a>
### Development and contributions

```sh
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv build
```

Tests cover search, API boundaries, document revisions, pagination, MCP calls, and project installation. [CI](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml) runs checks and builds on Linux, macOS, and Windows.

[tests/behavioral-cases.json](tests/behavioral-cases.json) contains proposed full-agent evaluation scenarios, not a claim that all agents have passed them. Native activation in each application's UI also needs verification after installation.

Contributions are welcome: reproducible bugs, new scenarios, and improvements to the source map, checks, and installation. Open an issue or pull request; add a focused regression test when changing logic.

### Distribution and license

Source code and release ZIPs are available on GitHub. Claude Code has a custom catalog. Submissions to the official Cursor and OpenAI directories have not been made. Bundled manifests do not constitute store listings.

For a complete Codex setup, use the project installer: the standalone Codex native manifest exposes only the skill. The Python wheel provides the MCP/CLI; obtain the installer and skill assets from the repository or release ZIP. Other agents can connect to the server if they support MCP over stdio, but dedicated installers are not yet included for them.

[MIT](LICENSE) covers original project code and instructions. Retrieved documentation retains its original ownership and terms; see [NOTICE](NOTICE).
