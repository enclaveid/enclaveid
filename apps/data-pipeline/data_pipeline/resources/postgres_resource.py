from contextlib import contextmanager
from typing import Iterator

import psycopg
from dagster import ConfigurableResource
from psycopg.abc import Query
from psycopg.rows import dict_row


class PostgresResource(ConfigurableResource):
    connection_string: str

    @contextmanager
    def get_connection(self) -> Iterator[psycopg.Connection]:
        """
        Creates and returns a database connection using psycopg3.
        Returns connection as a context manager that automatically closes when done.
        """
        conn = psycopg.connect(self.connection_string, row_factory=dict_row)  # type: ignore
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: Query, params: dict | None = None):
        """
        Executes a query and returns the results as a list of dictionaries.

        Args:
            query: SQL query string
            params: Optional dictionary of query parameters

        Returns:
            List of dictionaries where each dictionary represents a row
        """
        with self.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
