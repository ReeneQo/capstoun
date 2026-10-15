# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии — [SemVer](https://semver.org/lang/ru/).

## [1.1.0] — 2026-10-15

### Added

- Поле `created_at` у сообщений: время создания в UTC, возвращается в `GET` и `POST /messages`.

### Migration

- `ALTER TABLE messages ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
  Обратно совместима: v1.0.0 перечисляет колонки явно и не видит новую,
  а при вставке из v1.0.0 значение заполняет `DEFAULT`. Откат на v1.0.0 безопасен.

## [1.0.0] — 2026-10-15

### Added

- API гостевой книги: `GET /`, `GET /health`, `GET /messages`, `POST /messages`.
- `/health` проверяет соединение с базой и возвращает версию сервиса.
- Валидация входных данных и пагинация `?limit=` у списка сообщений.
- Пул соединений к PostgreSQL и идемпотентные миграции при старте.
- Docker-образ (не от root) и `compose.yaml` с healthcheck для `app` и `db`.
- CI: Ruff и pytest на каждый push и pull request.
- CD: публикация образа в ghcr.io из `main` (`:latest`) и по тегам `vX.Y.Z` для amd64 и arm64.
- README, RUNBOOK, CHANGELOG.

[1.1.0]: https://github.com/ReeneQo/capstoun/releases/tag/v1.1.0
[1.0.0]: https://github.com/ReeneQo/capstoun/releases/tag/v1.0.0
