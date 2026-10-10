# Удалённый MCP / Remote MCP deployment

## Русский

Удалённый MCP нужен для полного плагина в официальном каталоге OpenAI. Репозиторий предоставляет **Streamable HTTP**, контейнер и конфигурацию HTTPS через Caddy. Эти файлы не создают сервер, домен или заявку автоматически. Понадобится постоянный сервер с Docker Compose, свой DNS-домен, входящие порты 80/443 и доступ к аккаунту издателя.

### Развёртывание

1. Направьте DNS-запись выбранного поддомена на ваш сервер.
2. Скачайте репозиторий на сервер и скопируйте `deploy/.env.example` в `deploy/.env`.
3. В `deploy/.env` задайте реальный `MCP_DOMAIN` без протокола и пути.
4. Из корня репозитория запустите:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yml up --build -d
docker compose --env-file deploy/.env -f deploy/compose.yml ps
```

Caddy получает TLS-сертификат для указанного домена. MCP доступен по `https://ВАШ-ДОМЕН/mcp`; проверка процесса — `/healthz`. SQLite-кеш и сертификаты сохраняются в Docker volumes. Если сервер уже обслуживает сайты на портах 80/443, подключите MCP к существующему reverse proxy вместо запуска второго Caddy на тех же портах.

Домен явно разрешён в `TELEGRAM_MCP_ALLOWED_HOSTS` и его HTTPS origin — в `TELEGRAM_MCP_ALLOWED_ORIGINS`. Защита от DNS rebinding остаётся включённой. Локальный запуск без HTTPS для разработки:

```sh
uv run --frozen telegram-dev serve --transport streamable-http --host 127.0.0.1 --port 8000
```

Сервер читает только публичную документацию, не требует аккаунта Telegram и не выполняет действий в Telegram. Удалённые пользователи передают оператору аргументы инструментов и сетевые данные. До публичной подачи опубликуйте политику именно вашего сервиса: адрес, обработку журналов, сроки хранения и канал обращений. [Локальная политика](privacy.md) не подменяет её.

### Подтверждение домена и подача

Если кабинет OpenAI выдаст токен проверки, поместите его **точный текст** в `deploy/challenges/openai-apps-challenge`. Caddy отдаёт этот файл по `/.well-known/openai-apps-challenge`; файл исключён из Git. Подтверждение проверяется в кабинете, а не наличием конфигурации.

После проверки реального HTTPS endpoint и публикации политик соберите пакет:

```sh
uv run --frozen python scripts/package_openai.py --mcp-url "https://ВАШ-ДОМЕН/mcp" --privacy-url "https://АДРЕС-ПОЛИТИКИ" --terms-url "https://АДРЕС-УСЛОВИЙ" --demo-url "https://АДРЕС-ДЕМОВИДЕО"
```

Замените адреса на существующие публичные URL. Скрипт отвергает localhost, HTTP и шаблонные домены. Он создаёт ZIP, но не подаёт заявку. Проверьте SDK-подключение и все reviewer cases на развёрнутом сервере; затем выполните проверки и подачу через [OpenAI Plugins dashboard](https://platform.openai.com/plugins). [Требования всех каталогов](catalog-submissions.md).

## English

The complete OpenAI directory plugin requires a persistent HTTPS MCP. This repository provides Streamable HTTP, a non-root Docker image and a Caddy configuration; these assets do not provision hosting or submit a listing. Use your own Docker Compose server, DNS hostname, ports 80/443 and publisher account.

Point DNS to the server, copy `deploy/.env.example` to `deploy/.env`, set the real `MCP_DOMAIN`, then run `docker compose --env-file deploy/.env -f deploy/compose.yml up --build -d`. Caddy manages TLS. The MCP endpoint is `/mcp`, health is `/healthz`, and Docker volumes retain the documentation cache and certificates. Integrate with an existing reverse proxy when ports 80/443 are already in use.

The configured hostname/origin are explicitly allowed; DNS rebinding protection remains enabled. Local development can run `uv run --frozen telegram-dev serve --transport streamable-http --host 127.0.0.1 --port 8000`.

The service only reads public documentation. Remote operators receive tool arguments and network metadata and must publish policies describing their actual service and retention. The repository's local privacy policy does not cover a separate hosted operator.

For OpenAI domain verification, put the portal's exact token in `deploy/challenges/openai-apps-challenge`. Caddy serves it at `/.well-known/openai-apps-challenge`; the file is ignored by Git. Verify ownership in the portal. Build a remote submission ZIP with `scripts/package_openai.py`, supplying real HTTPS endpoint, privacy, terms and demo URLs. Then verify SDK connectivity and reviewer cases against that deployment and submit through the publisher portal. Preparing an archive does not prove submission or approval.
