# Конфиденциальность / Privacy

Обновлено / Updated: 2026-10-10.

## Русский

Telegram Dev — независимый открытый проект Kay0k1 для чтения публичной документации. Эта политика относится к скиллу, локальному плагину и локальному MCP из этого репозитория.

Отдельный пакет Telegram Dev Skill содержит только инструкции и справочные файлы. Он не запускает MCP, не создаёт кэш документации и не отправляет данные автору. Агент читает источники доступными ему инструментами; беседы и сетевые запросы обрабатываются платформой агента и посещаемыми сайтами по их правилам.

Локальный MCP получает от вашего агента поисковые запросы, URL публичных документов и параметры чтения. Он хранит загруженные документы, поисковый индекс, хэши, даты проверки и ошибки загрузки в локальном SQLite-кэше. Запросы поиска не записываются в этот индекс. Кэш сохраняется до удаления вами. По умолчанию файл `corpus.sqlite3` находится в системном каталоге кэша пользователя для `telegram-dev`; его путь можно задать через `TELEGRAM_KNOWLEDGE_DB`.

Для обновления MCP запрашивает разрешённые публичные страницы Telegram и выбранные файлы официальных репозиториев через HTTPS. Такие сайты получают обычные данные сетевого запроса, включая IP-адрес. Установка зависимостей через `uv` обращается к источникам пакетов. Агент и платформа, в которой он работает, обрабатывают вашу беседу по собственным правилам.

Проект не добавляет аналитику и не отправляет поисковые запросы автору. Доступ к аккаунтам Telegram, бот-токенам, личным сообщениям и контактам для работы с документацией не требуется. Не вставляйте секреты в запросы или публичные GitHub issues.

Если вы используете удалённый MCP, его оператор получает аргументы инструментов и сетевые запросы. Эта локальная политика не определяет правила отдельного сервера. Перед публичным запуском оператор должен опубликовать свою политику с адресом сервера, обработкой журналов, сроками хранения и способом обращения по вопросам данных.

Поддержка проекта: [GitHub issues](https://github.com/Kay0k1/telegram-dev/issues).

## English

Telegram Dev is an independent open-source documentation project maintained by Kay0k1. This policy covers the skill, local plugin and local MCP in this repository.

The separate Telegram Dev Skill package contains only instructions and reference files. It starts no MCP server, creates no documentation cache and sends no data to the author. The agent checks sources using its available tools; conversations and network requests are handled by the agent platform and visited websites under their own policies.

The MCP receives search text, public document URLs and reading parameters from your agent. It stores fetched documents, a search index, content hashes, check dates and fetch errors in a local SQLite cache. Search queries are not recorded in the index. The cache remains until you delete it. By default, `corpus.sqlite3` is in the operating system's user cache directory for `telegram-dev`; `TELEGRAM_KNOWLEDGE_DB` can override its path.

Refreshes fetch allowed public Telegram pages and selected files from official repositories over HTTPS. Those sites receive ordinary network metadata, including your IP address. Dependency installation with `uv` contacts package sources. Your agent platform processes your conversation under its own policies.

The project adds no analytics and does not send search queries to its author. Documentation access requires no Telegram account, bot token, private messages or contacts. Do not put secrets in prompts or public issues.

A remote MCP operator receives tool arguments and network requests. This local policy does not cover a separate hosted service. Before public deployment, the operator must publish the service URL, logging practices, retention and a data contact route in a service-specific policy.

Project support: [GitHub issues](https://github.com/Kay0k1/telegram-dev/issues).
