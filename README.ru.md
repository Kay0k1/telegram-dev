# Telegram Dev

[![Tests](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/telegram-dev)](https://pypi.org/project/telegram-dev/)
[![Docs monitor](https://github.com/Kay0k1/telegram-dev/actions/workflows/documentation.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/tree/docs-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Актуальная официальная документация Telegram и TON для Claude Code, Codex и Cursor.**

Telegram Dev — это MCP-сервер и скилл для агента. Сервер загружает, индексирует и ищет официальную документацию и следит, чтобы она не устаревала: Bot API, Mini Apps, MTProto, TDLib, а со стороны TON — docs.ton.org (TON Connect, Tolk, TVM, API), стандарты TEP и списки изменений. Скилл учит агента выбирать нужный API, соблюдать правила Telegram, проверять поддержку в библиотеке и указывать, откуда взяты сведения.

**Замер (Codex CLI, 11 задач, [evals](evals/README.md)):** когда у Codex есть свой доступ в интернет, плагин ничего не меняет (45/47 фактов из рубрик в обоих случаях); без интернета с Telegram Dev ответы остаются актуальными — 45/47 против 38/47 без него. Разницу дали Bot API 10.4 и новые названия монеты и кошелька TON.

[English](README.md)

## Зачем

Bot API выходит раз в месяц-два. Модель знает его только на дату своего обучения, поэтому агент уверенно пишет код с полями, которые уже изменились или которых никогда не было. Ещё агенты путают Bot API, MTProto и TDLib, а возможности у них сильно разные.

TON меняется так же быстро. В текущей документации TON монета называется Gram, описан Telegram Money — кошелёк внутри Telegram, а основной язык контрактов — Tolk, FunC стал устаревшим. Сверху — правила самого Telegram: блокчейн в Mini Apps только на TON и через TON Connect, цифровые товары — за Stars.

С Telegram Dev агент сначала читает актуальную страницу, потом пишет код. Настоящий прогон Codex CLI в новом проекте после `uvx telegram-dev install --agent codex` (вызовы сокращены):

```text
> Use the telegram-dev skill. In a python-telegram-bot project, I want the inline
  'Delete' button to be red and show a custom emoji. Which Bot API fields do this,
  what are the requirements, and what does the request JSON look like?

  telegram_corpus_status {}
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
```

Скилл знает и когда блокчейн *не* нужен. Ещё один настоящий прогон Codex:

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

## Установка

Нужен [uv](https://docs.astral.sh/uv/getting-started/installation/). Токен бота, аккаунт Telegram и ключи API не нужны: сервер читает только публичную документацию.

### MCP-сервер и скилл одной командой

Выполните в папке своего проекта:

```sh
uvx telegram-dev install --agent claude    # или codex, cursor
```

| `--agent` | Куда добавляется MCP-сервер | Куда копируется скилл |
| --- | --- | --- |
| `claude` | `.mcp.json` | `.claude/skills/telegram-dev` |
| `codex` | `.codex/config.toml` | `.agents/skills/telegram-dev` |
| `cursor` | `.cursor/mcp.json` | `.cursor/skills/telegram-dev` |

Установщик сохраняет остальные настройки, делает копии изменённых файлов и не перезаписывает уже установленный Telegram Dev. Сервер закреплён за установленной версией, поэтому кроме кэша uv на диске ничего держать не нужно. После установки откройте новую сессию агента и разрешите проектный MCP-сервер, если агент спросит. Codex читает настройки проекта, только когда папка проекта отмечена как доверенная.

Обновить: `uvx telegram-dev@latest install --agent claude --update`.

### Плагин Claude Code

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

Плагин подключает скилл и MCP-сервер сразу для всех проектов. Выберите плагин или установщик, но не оба.

### Только MCP-сервер

```sh
claude mcp add --scope user telegram-knowledge -- uvx telegram-dev serve
```

```sh
codex mcp add telegram-knowledge -- uvx telegram-dev serve
```

Cursor: [![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=telegram-knowledge&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJ0ZWxlZ3JhbS1kZXYiLCJzZXJ2ZSJdfQ%3D%3D)

Другие MCP-клиенты:

```json
{
  "mcpServers": {
    "telegram-knowledge": { "command": "uvx", "args": ["telegram-dev", "serve"] }
  }
}
```

Инструменты работают и без скилла, но именно скилл заставляет агента пользоваться ими каждый раз.

## Инструменты

| Инструмент | Что делает |
| --- | --- |
| `search_telegram_docs` | Полнотекстовый поиск по разделам, можно ограничить областью: `bot-api`, `mini-apps`, `telegram-api`, `tdlib`, `ton`, `releases`, `ton-releases` и другими |
| `get_telegram_document` | Читает официальную страницу частями до 40 000 символов; загружает её, если страницы нет или она старше 6 часов |
| `telegram_corpus_status` | Что проиндексировано, насколько свежее и какие источники не загрузились |
| `telegram_document_history` | Версии страницы, которые видела эта установка |
| `telegram_sources` | 57 официальных точек входа по областям API |

Кэш сначала пустой. Страница загружается, когда агент впервые её читает, и сразу индексируется. Загрузить заранее всё, что достижимо из настроенных источников:

```sh
uvx telegram-dev sync --max-pages 0
uvx telegram-dev search "sendVideoNote"
uvx telegram-dev status
```

## Что охватывает скилл

| Область | Что проверяет агент |
| --- | --- |
| Bot API | Сообщения, клавиатуры, обновления, вебхуки, файлы, права |
| Форматирование и эмодзи | Entities, смещения UTF-16, custom emoji и кому они доступны |
| Медиа и стикеры | Голосовые, кружки, стикерпаки, ограничения файлов |
| Mini Apps | JS-мост, параметры запуска, темы, проверка `initData` на сервере |
| MTProto и TDLib | Авторизация пользователя и бота, схема и слои, версии TDLib |
| Бизнес и платежи | Бизнес-подключения, Stars, подписки, подарки, платный контент |
| Группы и каналы | Права администраторов, форумы и темы, модерация |
| TON | Правила Telegram для блокчейна в Mini Apps, Stars или крипта, TON Connect и `ton_proof`, приём платежей, жетоны и NFT (TEP), контракты на Tolk, сначала testnet, безопасность ключей |
| Релизы | Changelog Bot API, слои API, changelog TDLib, changelog узла TON и Tolk, официальные анонсы |

Скилл лежит в [skills/telegram-dev](skills/telegram-dev/SKILL.md), по справочному файлу на каждую область.

## Насколько свежая документация

- Страница старше 6 часов при чтении загружается заново. Поиск обновляет до шести устаревших совпадений.
- Пока сервер работает, раз в 6 часов фоновый цикл проверяет до 120 страниц: точки входа, новые ссылки, самые старые страницы.
- Если сайт Telegram недоступен, сохраняется прежний текст с пометкой об устаревании и ошибкой, и агент видит, что читает старую копию.
- GitHub Action раз в сутки проверяет все 57 официальных источников и публикует хеши и ошибки в ветке [`docs-status`](https://github.com/Kay0k1/telegram-dev/tree/docs-status).

Путь к кэшу (`TELEGRAM_KNOWLEDGE_DB`) и интервалы обновления — в [docs/runtime.md](docs/runtime.md).

## Свой сервер

Сервер работает и по Streamable HTTP, чтобы команда пользовалась одним кэшем. В репозитории есть Dockerfile и настройка Caddy с HTTPS: [docs/deployment.md](docs/deployment.md).

```sh
uvx telegram-dev serve --transport streamable-http --port 8000
```

## Ограничения

- Поиск локальный полнотекстовый (SQLite FTS5), не семантический. Лучше всего работают точные имена методов и английские термины. Есть небольшая таблица русских синонимов.
- Охват — то, что достижимо из 57 официальных точек входа. Страницы TON берутся из оглавления `llms.txt`, которое docs.ton.org публикует для агентов, поэтому новые страницы подхватываются сами. История страницы начинается с её первой загрузки в вашей установке.
- Сервер не входит в Telegram, не отправляет сообщения, не трогает чаты и не хранит ключи кошельков. Он читает только публичные страницы.
- Скилл улучшает работу агента, но не гарантирует правильный ответ: проверяйте код в Telegram перед выкаткой.

## Разработка

```sh
git clone https://github.com/Kay0k1/telegram-dev && cd telegram-dev
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen telegram-dev install --agent claude --project /path/to/test-project
```

CI запускает тесты на Linux, macOS и Windows и проверяет Docker-образ. В [docs/validation.md](docs/validation.md) — что проверено вручную и что нет. Issues и pull requests приветствуются; в [tests/behavioral-cases.json](tests/behavioral-cases.json) — сценарии для агентов, которые ещё нужно прогнать в каждом клиенте.

## Лицензия

[MIT](LICENSE) для кода и скилла. Загруженная документация Telegram и TON остаётся у её владельцев, пакет её не содержит ([NOTICE](NOTICE)). Независимый проект, не связан с Telegram и TON Foundation.
