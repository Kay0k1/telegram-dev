# Telegram Dev

[![Tests](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/telegram-dev)](https://pypi.org/project/telegram-dev/)
[![Docs monitor](https://github.com/Kay0k1/telegram-dev/actions/workflows/documentation.yml/badge.svg)](https://github.com/Kay0k1/telegram-dev/tree/docs-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Чтобы Telegram-боты и ИИ-агенты работали с текущим Bot API.**

Telegram меняет Bot API раз в месяц-два, и отстают и код, и модели. В Telegram Dev три части:

- **`telegram-dev check`** читает Python-бота (aiogram, python-telegram-bot, pyTelegramBotAPI или прямые HTTP-запросы) и показывает вызовы Bot API с убранными параметрами или неверными значениями. Работает в терминале, в CI как GitHub Action или как инструмент агента.
- **Инструменты Bot API для агентов**: описания методов и типов, проверка запросов и changelog по версиям — всё строится из официальных страниц.
- **Сервер документации и скилл** для Claude Code, Codex и Cursor: поиск по официальной документации Telegram и TON (Bot API, Mini Apps, MTProto, TDLib, библиотеки ботов, TON Connect, Tolk), обновляется сам.

Аккаунт Telegram, токен бота и ключи API не нужны: всё читает публичную документацию.

[English](README.md)

## Проверка проекта бота

`telegram-dev check` за один запуск проверяет все вызовы Bot API в Python-боте — aiogram, python-telegram-bot, pyTelegramBotAPI или прямые HTTP-запросы к api.telegram.org — и выводит только находки:

```sh
uvx telegram-dev check ./my-bot
```

```text
$ uvx telegram-dev check ./tutorial        # популярный открытый учебник по aiogram 3
code/03_buttons/bot.py:79: warning: types.KeyboardButton: `request_user` was retired in Bot API 7.0: Renamed the field request_user in the class KeyboardButton to request_users. The old name will still work for backward compatibility. ...
code/08_inline_mode/handlers/inline_mode.py:48: warning: inline_query.answer: `switch_pm_text` was retired in Bot API 6.7: ... replacing the parameters switch_pm_text and switch_pm_parameter of the method answerInlineQuery with the parameter button of type InlineQueryResultsButton. ...
Bot API 10.4; 95 files with bot code; libraries: aiogram ==3.14.0 ==3.7.0 >=3.24.0 ...; 0 errors, 5 warnings
```

Неверное значение — ошибка: например, `InlineKeyboardButton(text="Delete", style="red")` даёт `style: must be one of danger, success, primary`.

Ошибки — значения вне списка из документации и несуществующие методы или параметры в прямых запросах к API. Предупреждения — параметры, которые Telegram убрал (с версией и записью changelog, где их заменили), именованные аргументы, которые не являются ни параметрами Bot API, ни известными опциями библиотек, и методы бота, которых нет в Bot API. Код читается без запуска, поэтому переменные не отслеживаются и обязательность параметров не проверяется. Опции: `--json`, `--exclude 'tests/*'`, `--strict` (падать и на предупреждениях), `--format github`. В сессии агента та же проверка — инструмент `check_telegram_project` (только у локального сервера stdio, потому что он читает файлы).

В репозитории на GitHub её можно запускать на каждый pull request — находки появятся аннотациями на изменённых строках:

```yaml
# .github/workflows/telegram.yml
on: [pull_request]
jobs:
  bot-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Kay0k1/telegram-dev@v0.9.0
        with:
          path: .
          exclude: "tests/*"
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

## Актуальная документация для агентов

Bot API выходит раз в месяц-два. Модель знает его только на дату своего обучения, поэтому агент уверенно пишет код с полями, которые уже изменились или которых никогда не было. Ещё агенты путают Bot API, MTProto и TDLib, а возможности у них сильно разные.

TON меняется так же быстро. В текущей документации TON монета называется Gram, описан Telegram Money — кошелёк внутри Telegram, а основной язык контрактов — Tolk, FunC стал устаревшим. Сверху — правила самого Telegram: блокчейн в Mini Apps только на TON и через TON Connect, цифровые товары — за Stars.

С Telegram Dev агент сначала читает актуальную страницу, потом пишет код. Настоящий прогон Codex CLI в новом проекте после `uvx telegram-dev install --agent codex` (вызовы сокращены):

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

## Инструменты

| Инструмент | Что делает |
| --- | --- |
| `search_telegram_docs` | Полнотекстовый поиск по разделам, можно ограничить областью: `bot-api`, `mini-apps`, `telegram-api`, `tdlib`, `ton`, `releases`, `ton-releases`, `aiogram`, `python-telegram-bot`, `grammy` и другими. Документация Telegram идёт первой, если в запросе не названа библиотека |
| `get_telegram_document` | Читает официальную страницу частями до 40 000 символов; загружает её, если страницы нет или она старше 6 часов |
| `get_telegram_corpus_status` | Что проиндексировано, насколько свежее и какие источники не загрузились |
| `list_telegram_document_revisions` | Версии страницы, которые видела эта установка |
| `list_telegram_sources` | 61 официальная точка входа по областям API |
| `list_telegram_cached_pages` | Страницы, которые уже лежат в локальном кэше, по областям, со свежестью |
| `get_bot_api_definition` | Один метод или тип Bot API в виде структуры: параметры или поля, типы, обязательность, допустимые значения, ограничения длины и записи changelog, где он упоминается |
| `check_bot_api_call` | Проверяет запрос, который отправляет ваш код, по текущей схеме Bot API: несуществующие методы и параметры (с подсказками), пропущенные обязательные, неверные типы, значения вне списка из документации, устаревшие параметры с версией, где их заменили |
| `list_bot_api_changes` | Changelog Bot API в виде структурированных выпусков, с фильтром по версии (`since_version="9.0"`) или по имени метода, типа или поля |
| `check_telegram_project` | Проверяет за один запуск все вызовы Bot API в локальном Python-проекте бота (см. [Проверка проекта бота](#проверка-проекта-бота)); только у локального сервера stdio |

### Проверка вызовов Bot API

Инструменты Bot API строятся из официальной страницы API и changelog в кэше, поэтому следуют текущей версии Telegram (на момент написания — Bot API 10.4) без схемы, написанной вручную. Например, `check_bot_api_call` для

```json
{"method": "sendMessage", "params": {"chat_id": 1, "text": "Delete?", "reply_to_message_id": 42,
  "reply_markup": {"inline_keyboard": [[{"text": "Delete", "callback_data": "del", "style": "red"}]]}}}
```

вернёт ошибку для `reply_markup.inline_keyboard[0][0].style` (допустимо только `danger`, `success`, `primary`) и предупреждение, что `reply_to_message_id` заменён на `reply_parameters` в Bot API 7.0. Telegram при этом не вызывается, так что права, состояние чата и содержимое файлов всё равно нужно проверять настоящим запуском.

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
| Библиотеки ботов | aiogram, python-telegram-bot и grammY: документация той версии, что стоит в проекте, сверка со страницей Bot API; агент говорит, если в индексе описана другая версия |
| Релизы | Changelog Bot API, слои API, changelog TDLib, changelog узла TON и Tolk, официальные анонсы |

Скилл лежит в [skills/telegram-dev](skills/telegram-dev/SKILL.md), по справочному файлу на каждую область.

## Насколько свежая документация

- Страница старше 6 часов при чтении загружается заново. Поиск обновляет до шести устаревших совпадений.
- Пока сервер работает, раз в 6 часов фоновый цикл проверяет до 120 страниц: точки входа, новые ссылки, самые старые страницы.
- Если сайт Telegram недоступен, сохраняется прежний текст с пометкой об устаревании и ошибкой, и агент видит, что читает старую копию.
- GitHub Action раз в сутки проверяет все 61 официальный источник и публикует хеши и ошибки в ветке [`docs-status`](https://github.com/Kay0k1/telegram-dev/tree/docs-status).

Путь к кэшу (`TELEGRAM_KNOWLEDGE_DB`) и интервалы обновления — в [docs/runtime.md](docs/runtime.md).

## Насколько это помогает

Замер на Codex CLI: 11 вопросов и 10 задач с кодом ([evals](evals/README.md)).

- Когда у Codex есть свой доступ в интернет, ответы одинаково правильные с Telegram Dev и без него: агент сам находит те же официальные страницы.
- Без доступа в интернет с Telegram Dev ответы остаются актуальными (45/47 фактов против 38/47, 26/26 проверок кода против 23/26); без него Codex не знал новейших возможностей Bot API и текущих названий в TON.

Так что сервер документации важнее всего там, где агент не может сам открыть сайт. Проверка проекта работает с вашим кодом, а не с вопросом, поэтому полезна в любом случае. На открытых ботах с GitHub она чаще всего находит `disable_web_page_preview` и `reply_to_message_id`, убранные в Bot API 7.0; Telegram и библиотеки пока принимают их ради совместимости. Подробности, включая разбор ложных срабатываний: [docs/validation.md](docs/validation.md).

## Свой сервер

Сервер работает и по Streamable HTTP, чтобы команда пользовалась одним кэшем. В репозитории есть Dockerfile и настройка Caddy с HTTPS: [docs/deployment.md](docs/deployment.md).

```sh
uvx telegram-dev serve --transport streamable-http --port 8000
```

## Ограничения

- Поиск локальный полнотекстовый (SQLite FTS5), не семантический. Лучше всего работают точные имена методов и английские термины. Есть небольшая таблица русских синонимов.
- Охват — то, что достижимо из 61 официальной точки входа. Страницы TON берутся из оглавления `llms.txt`, которое docs.ton.org публикует для агентов, поэтому новые страницы подхватываются сами. История страницы начинается с её первой загрузки в вашей установке.
- Библиотеки ботов: руководства и справка для ботов aiogram (`latest`, собирается из основной ветки), python-telegram-bot (документация `stable` и официальная вики) и grammY (английские руководства и плагины), около 250 страниц. Сгенерированные страницы отдельных типов, повторяющие Bot API, раздел `/ref/` grammY и переводы не индексируются; выпущенные версии aiogram и PTB (`/en/vX.Y.Z/`) читаются по запросу. Telegraf, Telethon и Pyrogram не индексируются.
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
