# Подача в каталоги / Directory submissions

Проверено: **2026-10-10**. Публичный исходный проект: [Kay0k1/telegram-dev](https://github.com/Kay0k1/telegram-dev).

**Заявки пока не отправлены.** Здесь нет receipt, идентификатора заявки или подтверждения приёма. Публикация репозитория и собственного каталога Claude Code не означает размещение в официальных каталогах. Перед новой подачей проверьте существующие заявки в соответствующем кабинете.

## Codex / OpenAI

Подача полного плагина проходит через [OpenAI Plugins dashboard](https://platform.openai.com/plugins). Нужны проверенная личность издателя и права владельца организации либо Apps Management Write. Для MCP требуется доступный удалённый HTTPS endpoint и подтверждение владения доменом. После проверок следует review, затем публикация. Изменения скилла и метаданных требуют нового ZIP. В уже созданный skills-only plugin нельзя добавить MCP. [Официальный процесс](https://developers.openai.com/plugins/deploy/submission), [упаковка и поддержка MCP](https://developers.openai.com/plugins/build/plugins).

В репозитории есть полный локальный Codex-плагин: скилл и MCP. Его встроенный stdio MCP использует `uv` и относительный `cwd` плагина. Этот вариант служит для локальной установки; он не выдаётся за remote submission package.

Собственный каталог Codex расположен в `.agents/plugins/marketplace.json`. Он позволяет установить плагин из репозитория через поддерживающий эти команды Codex CLI:

```sh
codex plugin marketplace add Kay0k1/telegram-dev
codex plugin add telegram-dev@telegram-dev-tools
```

Для разработки из клонированного репозитория вместо первой команды используйте `codex plugin marketplace add /absolute/path/to/telegram-dev`. Относительный `source.path: "./"` разрешается от корня репозитория, а не от каталога `.agents/plugins`. Установка требует доступный `uv`; затем начните новую сессию и проверьте MCP. Этот каталог доступен тем, кто добавил его источник, и не равнозначен официальной публичной выдаче. [Документация собственных каталогов Codex](https://developers.openai.com/plugins/build/plugins).

Нативная проверка выполнена на Codex CLI `0.162.1` в отдельном временном каталоге конфигурации без копирования авторизации: marketplace add, plugin add и native plugin/read прошли; app-server загрузил скилл и все пять MCP-инструментов из установленного кэша. Проверка использовала чистый экспорт файлов проекта, соответствующий свежему Git checkout. Вызовов модели и проверки интерфейса desktop в ней не было. При установке из локальной папки Codex копирует её содержимое в кэш, поэтому для распространения используйте чистый checkout без локальных секретов и окружений.

### Отдельный вариант без сервера

Если сейчас есть только аккаунт OpenAI, можно подготовить пакет с инструкциями и справочными материалами:

```sh
uv run --frozen python scripts/package_openai.py --skill-only
```

Результат: `dist/telegram-dev-skill-openai.zip`. У этой версии отдельное имя `telegram-dev-skill`; будущее полное размещение с MCP сохраняет имя `telegram-dev`. ZIP включает скилл, его справочные файлы, иконки, README, LICENSE и NOTICE. В нём нет конфигурации MCP, серверного кода, фонового обновления кэша или MCP-сценариев review. Агент проверяет актуальные страницы через уже доступный ему браузер или другие инструменты; без доступа к источникам обозначает непроверенные детали.

Домен и сервер этой упаковке не нужны. Требования кабинета к личности издателя и сканированию пакета сохраняются. Упаковка ещё не является заявкой или завершением задачи по размещению полного MCP-плагина. Выбор режима не отправляет ничего автоматически.

Для первой официальной подачи выбран именно **Telegram Dev Skill**. После сборки ZIP из окончательной версии проекта:

1. Войдите своим аккаунтом в [OpenAI Plugins](https://platform.openai.com/plugins), выберите организацию и проект. Нужны права владельца или Apps Management Write. Завершите individual verification в [Organization settings](https://platform.openai.com/settings/organization/general); проверка личности выполняется издателем в кабинете.
2. Сначала проверьте существующие drafts. Для новой заявки выберите **Upload new or existing plugin** / **Create plugin**, затем **Skills only**, свою проверенную Developer identity и файл `telegram-dev-skill-openai.zip`.
3. В **Metadata & Skills** проверьте импортированные значения и дождитесь scans. Required safety/security scans каждого скилла должны пройти; они могут занять до двух часов. Для исправления package-managed полей загрузите исправленный ZIP.
4. Выберите draft → **Submit for review**, заполните требуемые policy attestations. Сохраните URL/ID заявки, версию `0.3.0`, дату и подтверждённый Review status. После одобрения отдельно выберите **Publish plugin**.

| Поле skills-only пакета | Подготовленное значение |
| --- | --- |
| Package name | `telegram-dev-skill` |
| Display name | `Telegram Dev Skill` |
| Version | `0.3.0` |
| Category | `Developer Tools` |
| Subtitle | `Telegram development knowledge` |
| Русский subtitle | `Знания для разработки Telegram` |
| Website | `https://github.com/Kay0k1/telegram-dev` |
| Support | `https://github.com/Kay0k1/telegram-dev/issues` |
| Developer identity | Реальная проверенная личность владельца аккаунта; каталог использует её имя, независимо от `Kay0k1` в исходном manifest |
| MCP, domain challenge, review video, MCP test cases | Не входят в эту заявку |

Листинг и README в ZIP описывают инструкции и справочники, которые используют существующие инструменты агента для чтения актуальных источников. Они не обещают размещённый сервер, автоматическое обновление кеша или доступ к Telegram-аккаунтам. Скилл и справочники остаются частью открытого проекта. [Официальный upload/review workflow](https://developers.openai.com/plugins/deploy/submission), [skills-only путь](https://developers.openai.com/plugins/guides/submit-claude-plugin), [требования scans и package errors](https://developers.openai.com/plugins/deploy/submission-errors).

Вход через CLI Codex или GitHub не заменяет авторизацию издателя в Platform dashboard. Публичная инструкция описывает подачу через кабинет; отдельная команда CLI/API для официальной подачи в ней не указана. Отсутствие receipt означает, что заявку нельзя считать отправленной.

### Полный вариант с удалённым MCP

Для удалённой версии сначала разверните сервер, проверьте его HTTPS URL через настоящий MCP-клиент и опубликуйте политику/условия именно этого сервиса. Затем соберите отдельный ZIP:

```sh
uv run --frozen python scripts/package_openai.py \
  --mcp-url https://YOUR-DOMAIN/mcp \
  --privacy-url https://YOUR-DOMAIN/privacy \
  --terms-url https://YOUR-DOMAIN/terms \
  --demo-url https://YOUR-DOMAIN/demo.mp4 \
  --output dist/telegram-dev-openai.zip
```

Замените четыре URL реальными публичными адресами. Для этого режима обязательны адрес MCP, политика и условия конкретного сервиса, а также доступная демозапись. `--skill-only` и `--mcp-url` взаимоисключающие; сборщик отклоняет неполную конфигурацию, локальные адреса и URL-заглушки. Он не разворачивает сервер и не отправляет заявку. URL проверяются на формат; доступность, доменное подтверждение, совпадение политики с реальным сервисом и результаты сканирования проверяются отдельно. Сценарии в пакете — задания для reviewers, а не отчёт об их выполнении.

## Cursor

Официальная подача: [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Публичный репозиторий, валидный `.cursor-plugin/plugin.json`, документация и локальная проверка входят в [требования Cursor](https://cursor.com/docs/reference/plugins). Команда Cursor проверяет заявку.

В фактически загруженной форме на указанном адресе требуются вход в Cursor, имя, display name, доступный contact email, GitHub repository URL и HTTPS logotype URL. Поле описания и website URL необязательные. Submit означает принятие [Publisher Terms](https://cursor.com/marketplace-publisher-terms). Авторизация GitHub в терминале не авторизует этот кабинет.

Готовые значения после публикации файлов:

| Поле | Значение |
| --- | --- |
| Name | `telegram-dev` |
| Display name | `Telegram Dev` |
| Repository | `https://github.com/Kay0k1/telegram-dev` |
| Logo | `https://raw.githubusercontent.com/Kay0k1/telegram-dev/main/assets/logo.svg` |
| Website | `https://github.com/Kay0k1/telegram-dev` |
| Contact email | Реальный адрес издателя; в репозитории не придуман |

## Claude / Anthropic

Публичная подача доступна через [claude.ai/directory/manage](https://claude.ai/directory/manage). Нужны платный план с правом подачи, GitHub connection в той же Claude organization и push-доступ к репозиторию. Используйте Plugin bundle, repository `Kay0k1/telegram-dev`, корневой путь и branch `main`, затем validation, data handling, contact email, compliance и review. Не создавайте вторую заявку для того же repository/path. [Официальная инструкция](https://claude.com/docs/plugins/submit).

Anthropic Directory и `claude-plugins-official` — разные пути распространения. Установка из Directory доходит до Claude Code через синхронизацию аккаунта; для official-marketplace listing документация направляет к Anthropic partner contact. Отдельный remote MCP также подаётся как connector. [Публикация плагинов Claude Code](https://code.claude.com/docs/en/plugins/publish).

Собственный каталог уже доступен из публичного репозитория:

```text
/plugin marketplace add Kay0k1/telegram-dev
/plugin install telegram-dev@telegram-dev-tools
```

Обновление документации происходит в MCP. Обновление кода плагина — отдельный процесс: повышайте `version` при каждом релизе и используйте механизм обновления marketplace. В пользовательском каталоге Claude auto-update по умолчанию выключен; пользователь включает его в настройках. [Установка и обновления Claude Code](https://code.claude.com/docs/en/discover-plugins).

## Что доказывает состоявшуюся подачу

Для каждой площадки сохраните URL заявки или её ID, дату, отправленный commit/version, подтверждённый status и следующий шаг. `Prepared`, `Uploaded`, `Submitted`, `Approved` и `Published` — разные состояния. Запись «Submitted» добавляется только после подтверждения кабинета; наличие ZIP, манифеста или зелёных тестов этого не доказывает.

## English

No official directory submission has been sent or acknowledged. The local project includes skills and MCP. For an independent instructions-only OpenAI variant, build with `scripts/package_openai.py --skill-only`; the result uses the separate identity `telegram-dev-skill` and checks current sources through the agent's existing tools. It bundles no documentation server or background cache updater. The complete `telegram-dev` directory plugin still needs a verified publisher, remote HTTPS MCP, service policies and demo recording. The builder prepares archives and never submits them. Cursor and Anthropic submission routes remain described above.

Record an actual receipt, submission URL or ID before claiming submission. Keep code versions and documentation-cache freshness separate, and recheck official requirements before release.
