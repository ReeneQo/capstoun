from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status

from app import repository
from app.config import get_settings
from app.db import DbConnection, create_pool, migrate
from app.schemas import MessageIn, MessageOut


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with create_pool(get_settings().database_conninfo) as pool:
        migrate(pool)
        app.state.pool = pool
        yield


app = FastAPI(title="guestbook", version=get_settings().app_version, lifespan=lifespan)


@app.get("/")
def index() -> dict[str, str]:
    return {"message": get_settings().greeting}


@app.get("/health")
def health(conn: DbConnection) -> dict[str, str]:
    conn.execute("SELECT 1")
    return {"status": "ok", "version": get_settings().app_version}


@app.get("/messages")
def list_messages(
    conn: DbConnection,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[MessageOut]:
    return repository.list_messages(conn, limit)


@app.get("/messages/{message_id}")
def get_message(message_id: int, conn: DbConnection) -> MessageOut:
    message = repository.get_message(conn, message_id)
    if message is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    return message


@app.post("/messages", status_code=status.HTTP_201_CREATED)
def add_message(message: MessageIn, conn: DbConnection) -> MessageOut:
    return repository.add_message(conn, message)
