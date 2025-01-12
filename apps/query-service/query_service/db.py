import os

import psycopg
from psycopg.rows import dict_row


def get_user_id_from_api_key(api_key):
    """Authenticate API key and return user ID."""
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise ValueError("DATABASE_URL environment variable is not set")

    with (
        psycopg.connect(conn_string, row_factory=dict_row) as conn,
        conn.cursor() as cur,
    ):
        cur.execute('SELECT id FROM "User" WHERE "apiKey" = %s', (api_key,))
        result = cur.fetchone()
        if not result:
            return None
        return result["id"]
