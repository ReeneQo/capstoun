from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from psycopg import Connection
from psycopg_pool import ConnectionPool

MIGRATIONS = (
    """
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        author TEXT NOT NULL,
        text TEXT NOT NULL
    )
    """,
)


def create_pool(conninfo: str) -> ConnectionPool:
    return ConnectionPool(conninfo, min_size=1, max_size=10, timeout=5, open=False)


def migrate(pool: ConnectionPool) -> None:
    with pool.connection() as conn:
        for statement in MIGRATIONS:
            conn.execute(statement)


def get_connection(request: Request) -> Iterator[Connection]:
    pool: ConnectionPool = request.app.state.pool
    with pool.connection() as conn:
        yield conn


DbConnection = Annotated[Connection, Depends(get_connection)]
