from psycopg import Connection
from psycopg.rows import class_row

from app.schemas import MessageIn, MessageOut


def list_messages(conn: Connection, limit: int) -> list[MessageOut]:
    with conn.cursor(row_factory=class_row(MessageOut)) as cur:
        cur.execute(
            "SELECT id, author, text, created_at FROM messages "
            "ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def add_message(conn: Connection, message: MessageIn) -> MessageOut:
    with conn.cursor(row_factory=class_row(MessageOut)) as cur:
        cur.execute(
            "INSERT INTO messages (author, text) VALUES (%s, %s) "
            "RETURNING id, author, text, created_at",
            (message.author, message.text),
        )
        created = cur.fetchone()
    if created is None:
        raise RuntimeError("INSERT ... RETURNING returned no row")
    return created
