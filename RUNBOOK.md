# 🚨 RUNBOOK — guestbook

Аварийная инструкция: что делать, когда что-то пошло не так. Команды выполняются
на сервере в каталоге с `compose.yaml` и `.env`.

## Паспорт сервиса

| Что               | Где                                                    |
| ----------------- | ------------------------------------------------------ |
| Образы            | `ghcr.io/reeneqo/capstoun:<версия>`                          |
| Текущая версия    | `curl -s localhost:8000/health` → поле `version`        |
| Конфигурация      | `.env` (шаблон — `.env.example`)                        |
| Данные            | volume `pgdata` (сервис `db`, PostgreSQL 16)            |
| Логи              | `docker compose logs -f app` / `docker compose logs db` |
| Список релизов    | `CHANGELOG.md`, вкладка Packages на GitHub              |

## 1. Сервис не отвечает

```bash
docker compose ps                         # кто не healthy / перезапускается?
docker compose logs --tail=100 app        # трейсбек приложения
docker compose logs --tail=50 db
curl -sf localhost:8000/health || echo DOWN
```

| Симптом                                    | Вероятная причина         | Действие                                  |
| ------------------------------------------ | ------------------------- | ----------------------------------------- |
| `app` в `Restarting`, в логах `PoolTimeout` | база недоступна          | см. п. 3                                   |
| `ValidationError` при старте                | нет переменной в `.env`   | сверить `.env` с `.env.example`           |
| `/health` → 500 после выката                | баг в новой версии        | **откат**, п. 2                            |
| `manifest unknown` при `pull`               | опечатка в теге / CI не допубликовал | проверить тег в Packages       |
| `unauthorized` при `pull`                   | нет доступа к ghcr.io     | `docker login ghcr.io` (PAT с `read:packages`) |

## 2. Откат на предыдущую версию

Главное правило: **сначала откатить, потом разбираться.**

```bash
curl -s localhost:8000/health                              # 1. какая версия сейчас
APP_TAG=1.0.0 docker compose pull app                      # 2. предыдущий тег из CHANGELOG.md
APP_TAG=1.0.0 docker compose up -d --no-build --wait app   # 3. перезапуск на старом образе
curl -s localhost:8000/health                              # 4. version == 1.0.0, status == ok
curl -s localhost:8000/messages | head -c 300              # 5. данные на месте
```

Затем зафиксировать версию в `.env` (`APP_TAG=1.0.0`), чтобы случайный
`docker compose up` не вернул сломанный релиз.

Откат безопасен для данных, потому что миграции только расширяющие: старый код
не знает о новых колонках и не трогает их (подробнее — README, «Почему такая стратегия»).
Если релиз всё же содержал ломающую миграцию — **не откатывать вслепую**, сначала
бэкап (п. 4), затем ручное восстановление схемы.

## 3. Проблемы с базой

```bash
docker compose exec db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose restart db
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\d messages'
```

⚠️ Никогда не выполнять `docker compose down -v` на проде — `-v` удаляет volume с данными.

## 4. Бэкап и восстановление

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%F_%H%M).sql
docker compose exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backup_YYYY-MM-DD_HHMM.sql
```

Перед `pg_dump`/`psql` выполнить `set -a; source .env; set +a`, чтобы подставились переменные.

## 5. Выкат новой версии

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_before_X.Y.Z.sql
APP_TAG=X.Y.Z docker compose pull app
APP_TAG=X.Y.Z docker compose up -d --no-build --wait app
curl -s localhost:8000/health
```

Если `--wait` упал или `/health` не `ok` — сразу п. 2. После успешного выката
записать `APP_TAG=X.Y.Z` в `.env`.

## 6. Утёк пароль от базы

1. Сменить пароль в базе:
   `docker compose exec db psql -U "$POSTGRES_USER" -c "ALTER USER $POSTGRES_USER PASSWORD 'новый'"`.
2. Обновить `POSTGRES_PASSWORD` в `.env`.
3. `docker compose up -d --no-build --wait app`.

Переменная `POSTGRES_PASSWORD` у контейнера `db` влияет только на первую инициализацию
volume, поэтому пароль меняется именно через `ALTER USER`.
