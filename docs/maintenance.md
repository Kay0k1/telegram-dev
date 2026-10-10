# Обновление Telegram Dev / Keeping Telegram Dev current

## Русский

Telegram Dev разделяет обновление документации и обновление самого инструмента. Проверка новых страниц не устанавливает новую версию кода и не гарантирует, что агент правильно применил найденное правило.

### Ежедневная проверка источников

GitHub Actions запускает [Official documentation monitor](https://github.com/Kay0k1/telegram-dev/actions/workflows/documentation.yml) каждый день около 06:23 UTC. Расписание GitHub [может запускаться с задержкой](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). Проверку можно запустить вручную через **Run workflow**. GitHub также может [отключить расписание публичного репозитория после 60 дней без активности](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows); его можно включить снова на странице Actions.

Workflow проверяет все официальные входные страницы из `SEEDS` в `telegram_knowledge.py`: Bot API и его changelog, Mini Apps, Telegram API/MTProto и TL schema, TDLib и его schema/changelog, Telegram Desktop changelog, форматирование, эмодзи, стикеры, файлы, платежи, Gateway, веб-интеграции и новости продукта. При добавлении нового seed он автоматически попадёт в следующую проверку. Это наблюдение за входными страницами, а не ежедневный обход каждого символа API или исторической версии документации.

Результаты доступны в публичной ветке [docs-status](https://github.com/Kay0k1/telegram-dev/tree/docs-status):

- `README.md` — время проверки и состояние каждой страницы.
- `source-snapshot.json` — последний успешный SHA-256 извлечённого текста, название, URL, семейство, время проверки и обнаружения изменения.
- `source-report.json` — точные состояния `new`, `changed`, `unchanged`, `failed`, предыдущий и текущий хэш, ошибки загрузки.

Первый запуск создаёт исходный снимок (`new`). Следующие запуски сравниваются с опубликованным снимком; GitHub cache используется как резерв. При ошибке старый успешный хэш сохраняется, страница отмечается как `failed`, а workflow завершается с ошибкой. Поэтому устаревшая запись никогда не выдаётся за свежую проверку. В каждом запуске также сохраняется артефакт метаданных на 30 дней.

Хэш считается по извлечённому тексту документа после обработки `telegram_knowledge.fetch`. Изменение хэша говорит об изменении текста, но не объясняет, какая функция добавлена или удалена. Workflow не придумывает описание релиза и не создаёт issues с уведомлениями. Полный текст сторонней документации в ветку не публикуется.

### Проверка локально

Из корня клонированного репозитория:

```sh
uv run --frozen python scripts/check_sources.py --output .source-monitor/current
uv run --frozen python scripts/check_sources.py --previous .source-monitor/current/source-snapshot.json --output .source-monitor/next
```

Для быстрой проверки одного источника:

```sh
uv run --frozen python scripts/check_sources.py --source https://core.telegram.org/bots/api --output .source-monitor/bot-api
```

Не используйте снимок одной страницы как полную исходную базу ежедневного workflow. Если проверяемый список изменился, добавленные страницы будут отмечены как `new`. В каждом запуске не более четырёх одновременных запросов; по умолчанию есть одна повторная попытка при ошибке.

### Ответственность за актуальность

Публичный монитор показывает, что официальные источники доступны и когда их текст изменялся. Локальная база документации у каждого пользователя обновляется отдельно через MCP/runtime. Состояние `docs-status` не доказывает, что пользовательская база или сессия агента уже прочитала новую версию.

Новые возможности Telegram требуют проверки текущего официального источника, условий доступа и поддержки клиентом/SDK. Если изменилась семантика функции, сопровождающий обновляет скилл и примеры, проверяет поведенческие сценарии и выпускает новую версию инструмента.

## English

Telegram Dev treats source updates and tool releases separately. A successful source check does not install new code or prove an agent applied a feature correctly.

The [Official documentation monitor](https://github.com/Kay0k1/telegram-dev/actions/workflows/documentation.yml) checks every configured `SEEDS` entry daily around 06:23 UTC and supports **Run workflow**. GitHub may [delay scheduled runs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) or [disable schedules in public repositories after 60 days of inactivity](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows); re-enable the schedule in Actions when needed.

Coverage includes Bot API/changelog, Mini Apps, Telegram API/MTProto/TL schema, TDLib/schema/changelog, Desktop changelog, formatting, emoji, stickers, files, payments, Gateway, web integrations and product news. This is an entry-point monitor rather than a daily full crawl of every API symbol and historical document.

The public [docs-status branch](https://github.com/Kay0k1/telegram-dev/tree/docs-status) contains a human-readable status, `source-snapshot.json` with successful hashes and timestamps, and `source-report.json` with exact `new`, `changed`, `unchanged` and `failed` results. The published snapshot is the next run's checkpoint, with Actions cache as a fallback. Failed downloads preserve the previous successful record, remain explicitly failed and make the workflow fail. Each run uploads a metadata artifact retained for 30 days.

SHA-256 hashes cover the extracted document text returned by `telegram_knowledge.fetch`. A changed hash does not infer feature semantics. No generated release summary, issue notification or third-party full document text is published.

Run `uv run --frozen python scripts/check_sources.py --output .source-monitor/current` locally. Pass `--previous PATH/source-snapshot.json` for comparison or `--source https://core.telegram.org/bots/api` for a focused check. Requests are bounded to four workers, with two attempts per source by default.

Every user's runtime documentation cache is separate from this public status. Source monitoring cannot prove their local cache or active agent session has refreshed. Maintainers must still verify feature changes, update skill instructions/examples, run behavioral checks and release new tool versions when behavior changes.
