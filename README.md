# 📒 guestbook

[![CI/CD](https://github.com/ReeneQo/capstoun/actions/workflows/ci.yml/badge.svg)](https://github.com/ReeneQo/capstoun/actions/workflows/ci.yml)

Гостевая книга на **FastAPI + PostgreSQL**, доведённая до прода: CI на каждый push,
образы в GitHub Container Registry, версионированные релизы по git-тегам и
проверенный откат на предыдущую версию.

> Капстоун курса: оценивается не бизнес-логика, а путь кода от коммита до прода.

## API

| Метод  | Путь        | Что делает                                                       |
| ------ | ----------- | ---------------------------------------------------------------- |
| `GET`  | `/`         | приветствие                                                      |
| `GET`  | `/health`   | жив ли сервис и его база; возвращает версию: `{"status": "ok", "version": "1.0.0"}` |
| `GET`  | `/messages` | сообщения, новые сверху; `?limit=1..100` (по умолчанию 50)       |
| `POST` | `/messages` | добавить сообщение `{"author": "...", "text": "..."}` → `201`    |

Интерактивная документация — <http://localhost:8000/docs>.

## 🚀 Быстрый старт

```bash
cp .env.example .env        # задайте POSTGRES_PASSWORD
docker compose up -d --build --wait
curl http://localhost:8000/health
```

`--wait` дожидается, пока healthcheck приложения станет `healthy`, — если сервис
не поднялся, команда завершится ошибкой, а не «молча успехом».

## 🧪 Разработка

```bash
uv sync                                   # зависимости из uv.lock в .venv
docker run -d --name guestbook-db -p 5432:5432 \
  -e POSTGRES_USER=guestbook -e POSTGRES_PASSWORD=guestbook -e POSTGRES_DB=guestbook \
  postgres:16-alpine                      # база для тестов и локального запуска
uv run uvicorn app.main:app --reload      # http://localhost:8000
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

Тесты — интеграционные: ходят в настоящий PostgreSQL, как и в CI.

## 🏗️ Как устроено

```
app/
  config.py      настройки на pydantic-settings (env / .env), пароль — SecretStr
  db.py          пул соединений, миграции, зависимость FastAPI DbConnection
  schemas.py     входные и выходные модели с валидацией
  repository.py  SQL-запросы (только параметризованные)
  main.py        приложение и эндпоинты
tests/           интеграционные тесты API
```

- **Зависимости** — uv: `pyproject.toml` + `uv.lock`, Python закреплён в `.python-version`.
- **Конфиг** — `app/config.py`; секреты только в `.env` (в `.gitignore`), в репозитории — `.env.example`.
- **Образ** — зависимости ставятся до копирования кода (кэш слоёв), процесс работает не от root,
  версия зашивается в образ через `--build-arg APP_VERSION`.
- **Compose** — `app` + `db`; база доступна по имени сервиса `db`, данные в volume `pgdata`,
  `app` стартует только после `service_healthy` базы.

## 🔁 Конвейер

```
push / PR ──► check: ruff + pytest (с Postgres)
                 │ зелёный
                 ▼
push в main ──► publish ──► ghcr.io/reeneqo/capstoun:latest, :sha-xxxxxxx
тег vX.Y.Z  ──► publish ──► ghcr.io/reeneqo/capstoun:X.Y.Z, :X.Y
```

- `publish` зависит от `check` (`needs: check`) — красный CI образ не публикует.
- Из PR и feature-веток образы не публикуются, только из `main` и тегов.
- `:latest` двигается только из `main`; версионные теги неизменяемы — на них и строится откат.

## 🏷️ Релиз

1. Обновить `CHANGELOG.md` и `version` в `pyproject.toml`, закоммитить в `main`.
2. Поставить тег и запушить:
   ```bash
   git tag -a v1.1.0 -m "v1.1.0"
   git push origin v1.1.0
   ```
3. Дождаться зелёного workflow — в Packages появится образ `:1.1.0`.

Версии — по [SemVer](https://semver.org/lang/ru/): `MAJOR` — ломающие изменения API,
`MINOR` — новая функциональность, `PATCH` — исправления.

## 🚢 Выкат и откат

Сервер работает с готовыми образами из ghcr.io, версия задаётся переменной `APP_TAG`:

```bash
APP_TAG=1.1.0 docker compose pull app
APP_TAG=1.1.0 docker compose up -d --no-build --wait app   # выкат
APP_TAG=1.0.0 docker compose up -d --no-build --wait app   # откат
curl http://localhost:8000/health                          # смотрим version
```

Подробно, с диагностикой и аварийными сценариями, — в [RUNBOOK.md](RUNBOOK.md).

### Почему такая стратегия

**Неизменяемые образы + перезапуск на нужный тег.** Каждый релиз — отдельный образ
с фиксированной версией, поэтому откат — это не «пересобрать старый код», а запустить
уже проверенный образ: секунды и без сюрпризов. Для одного сервера это проще и
надёжнее blue/green; цена — короткий простой при пересоздании контейнера.

**Миграции только расширяющие (expand-only).** Откат кода не откатывает базу, поэтому
схема каждой версии обязана работать со старым кодом:

- можно: новая таблица, новая колонка с `DEFAULT` или nullable, новый индекс;
- нельзя в том же релизе: удалить/переименовать колонку, сменить тип, добавить
  `NOT NULL` без `DEFAULT`.

Миграции идемпотентны (`IF NOT EXISTS`) и применяются при старте приложения.
