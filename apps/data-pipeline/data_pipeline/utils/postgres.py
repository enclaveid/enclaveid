from typing import Iterable

from pandas.io import sql
from psycopg import Connection
from sqlalchemy import make_url
from sqlalchemy.dialects.postgresql import insert


def conn_string_to_conn_args(conn_string: str):
    url = make_url(conn_string)
    return {
        "host": url.host,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "dbname": url.database,
    }


def pg_insert_on_conflict_replace(
    table: sql.SQLTable, conn: Connection, keys: list, data_iter: Iterable
):
    stmt = insert(table).values(list(data_iter))
    upsert_stmt = stmt.on_conflict_do_update(index_elements=keys)
    conn.execute(upsert_stmt)
