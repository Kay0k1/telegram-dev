# Автообновление документации / Automatic documentation refresh

## Русский

Начиная с 0.3.0, MCP автоматически проверяет свежесть документа при чтении. По умолчанию страница считается устаревшей через **6 часов**. Поиск обновляет до шести устаревших найденных страниц, затем повторяет поиск: удалённые сведения не остаются в результатах как актуальные.

`refresh=true` в `get_telegram_document` принудительно проверяет источник даже до истечения этого срока. В ответах есть `freshness.stale`, `age_seconds`, `max_age_seconds`, `refresh_error`, хэш и дата последней успешной проверки. Если сайт недоступен, ранее загруженный текст сохраняется с явной отметкой об ошибке. Успех не имитируется, дата проверки не переносится вперёд. Автоматические повторные запросы к недоступной странице ограничены интервалом 15 минут; принудительное обновление обходит этот интервал.

Пока MCP запущен, фоновая задача каждые 6 часов обрабатывает до **120 страниц**. Она проверяет входные источники, расширяет обнаруженный набор документов и возвращается к старым страницам. Расписание хранится в общей SQLite-базе, поэтому несколько проектов, использующих один кеш, не начинают отдельный обход при каждом запуске. Первое подключение запускает проверку в фоне и не ждёт загрузки всей базы.

Это постепенное заполнение кеша. Для полного первоначального обхода используйте `uv run --frozen telegram-dev sync --max-pages 0`. Его завершение и недоступные источники проверяйте через `telegram-dev status`; количество страниц само по себе не доказывает полноту знаний Telegram. `telegram_sources` перечисляет настроенные точки входа; живые API indexes и schema позволяют находить дополнительные функции.

Настройки задаются в окружении MCP-сервера:

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `TELEGRAM_KNOWLEDGE_DB` | Пользовательский кеш ОС | Путь к SQLite-базе |
| `TELEGRAM_DOC_MAX_AGE_SECONDS` | `21600` | Максимальный возраст страницы; `0` — проверять каждое чтение |
| `TELEGRAM_DOC_AUTO_SYNC` | `1` | `0` отключает фоновые обходы; чтение старых страниц всё ещё проверяет источник |
| `TELEGRAM_DOC_SYNC_INTERVAL_SECONDS` | `21600` | Интервал фонового обхода; минимум 60 секунд |
| `TELEGRAM_DOC_SYNC_PAGES` | `120` | Бюджет страниц за один обход; минимум 1 |
| `TELEGRAM_DOC_RETRY_SECONDS` | `900` | Пауза автоматических повторов после ошибки |

Для одного ручного ограниченного обхода:

```sh
uv run --frozen telegram-dev maintain --max-pages 120
```

Статус сообщает число устаревших страниц, ошибки, параметры обновления, время следующего запланированного обхода и отчёт о последнем завершённом. Когда процесс MCP остановлен, фоновые задачи не выполняются. На постоянно работающем сервере обновления продолжаются между сессиями пользователей.

### Обновление самого скилла

Документация и программные релизы обновляются раздельно. Для установки через проектный установщик:

```sh
git pull --ff-only
uv run --frozen python scripts/install.py --agent codex --project "/absolute/path/to/your-project" --update
```

Выберите свой `--agent`. Обновление переносит новый скилл и проверяет подключение MCP, сохраняя остальные настройки и резервные копии. При локальных изменениях скилла или чужом подключении оно останавливается. Установки 0.2.0 не имеют ownership manifest: перед миграцией сохраните свою папку скилла и конфигурацию, удалите старые записи Telegram Dev и установите заново. Новая версия поддерживает последующие обновления через `--update`.

В каталогах используйте механизм обновления самой площадки. Для скиллов и метаданных OpenAI требуется новый проверенный пакет; обновление источников в удалённом MCP не требует нового скилла на каждую страницу. [Подача и обновления каталогов](catalog-submissions.md), [ежедневный монитор](maintenance.md).

## English

From 0.3.0, reading a document automatically refreshes pages older than **6 hours** by default. Search refreshes up to six stale matching pages and reruns the query. `get_telegram_document` accepts `refresh=true` for an immediate live check. Responses expose `freshness.stale`, age, the refresh policy and any refresh error, alongside source hashes and successful check timestamps.

Source failures preserve previously cached text and explicitly mark it stale; they never advance the successful check date. Automatic retries wait 15 minutes by default; forced refresh bypasses that backoff.

While the MCP process runs, a background cycle every 6 hours checks up to **120 pages**, covering entrypoints, new discovered links and older documents. Its SQLite schedule is shared between projects using the same cache. Startup does not wait for a full corpus. Coverage expands gradually; use `uv run --frozen telegram-dev sync --max-pages 0` for a complete initial crawl of the discovered scope and inspect `telegram-dev status` for gaps. `telegram_sources` lists configured entrypoints; follow the live API indexes and schema for further features.

The environment settings in the table above control the database, age threshold, background enablement, interval, page budget and retry backoff. Run `uv run --frozen telegram-dev maintain --max-pages 120` for one bounded cycle. Background work requires a running server; a permanently hosted MCP continues refreshing between user sessions.

Code and skill releases are separate from documentation checks. For project installs, update the checkout with `git pull --ff-only`, then rerun `scripts/install.py` with your original agent/project and `--update`. It preserves unrelated configuration, creates backups and refuses to overwrite local skill edits or an unmanaged connection. Version 0.2.0 installs have no ownership marker: back up and remove the old Telegram Dev skill and MCP entry before reinstalling once. Marketplace installs use their platform's update mechanism. OpenAI skill/metadata changes require a new reviewed package; remote documentation cache updates do not.
