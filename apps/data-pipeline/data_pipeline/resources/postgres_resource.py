"""Credit: Dagster Labs. RedshiftClient and RedshiftClientResource shipped in
dagster_aws modified to use psycopg3 (instead of v2)."""

from contextlib import contextmanager
from logging import Logger
from typing import Any, Dict, Optional

import dagster._check as check
import psycopg
from dagster import ConfigurableResource, get_dagster_logger
from pgvector.psycopg import register_vector
from pydantic import Field

# TODO: Why do we need this? Super ugly.


class PostgresClient:
    def __init__(
        self, conn_args: Dict[str, Any], autocommit: Optional[bool], log: Logger
    ):
        # Extract parameters from resource config
        self.conn_args = conn_args

        self.autocommit = autocommit
        self.log = log

    def execute_query(
        self,
        query,
        fetch_results=False,
        cursor_factory=psycopg.Cursor,
        error_callback=None,
    ):
        """Synchronously execute a single query against Postgres. Will return a list of rows, where
        each row is a tuple of values, e.g. SELECT 1 will return [(1,)].

        Args:
            query (str): The query to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            cursor_factory (Optional[:py:class:`psycopg2.extensions.cursor`]): An alternative
                cursor_factory; defaults to None. Will be used when constructing the cursor.
            error_callback (Optional[Callable[[Exception, Cursor, DagsterLogManager], None]]): A
                callback function, invoked when an exception is encountered during query execution;
                this is intended to support executing additional queries to provide diagnostic
                information, e.g. by querying ``stl_load_errors`` using ``pg_last_copy_id()``. If no
                function is provided, exceptions during query execution will be raised directly.

        Returns:
            Optional[List[Tuple[Any, ...]]]: Results of the query, as a list of tuples, when
                fetch_results is set. Otherwise return None.
        """
        check.str_param(query, "query")
        check.bool_param(fetch_results, "fetch_results")
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg.Cursor
        )
        check.opt_callable_param(error_callback, "error_callback")

        with self._get_conn(cursor_factory=cursor_factory) as conn:
            with self._get_cursor(conn) as cursor:
                try:
                    self.log.info(f"Executing query '{query}'")
                    cursor.execute(query)

                    if fetch_results and cursor.rowcount > 0:
                        return cursor.fetchall()
                    else:
                        self.log.info("Empty result from query")

                except Exception as e:
                    # If autocommit is disabled or not set (it is disabled by default), Postgres
                    # will be in the middle of a transaction at exception time, and because of
                    # the failure the current transaction will not accept any further queries.
                    #
                    # This conn.commit() call closes the open transaction before handing off
                    # control to the error callback, so that the user can issue additional
                    # queries. Notably, for e.g. pg_last_copy_id() to work, it requires you to
                    # use the same conn/cursor, so you have to do this conn.commit() to ensure
                    # things are in a usable state in the error callback.
                    if not self.autocommit:
                        conn.commit()

                    if error_callback is not None:
                        error_callback(e, cursor, self.log)
                    else:
                        raise

    @contextmanager
    def _get_conn(self, cursor_factory=psycopg.Cursor):
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg.Cursor
        )

        conn = None
        try:
            conn = psycopg.connect(**self.conn_args, cursor_factory=cursor_factory)
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def _get_cursor(self, conn):
        # Could be none, in which case we should respect the connection default. Otherwise
        # explicitly set to true/false.
        if self.autocommit is not None:
            conn.autocommit = self.autocommit

        with conn:
            with conn.cursor() as cursor:
                yield cursor

            # If autocommit is set, we'll commit after each and every query execution. Otherwise, we
            # want to do a final commit after we're wrapped up executing the full set of one or more
            # queries.
            if not self.autocommit:
                conn.commit()


class PGVectorClient(PostgresClient):
    @contextmanager
    def _get_conn(self, cursor_factory=psycopg.Cursor):
        check.opt_class_param(
            cursor_factory, "cursor_factory", superclass=psycopg.Cursor
        )

        conn = None
        try:
            conn = psycopg.connect(**self.conn_args, cursor_factory=cursor_factory)
            register_vector(conn)
            yield conn
        finally:
            if conn:
                conn.close()


class PostgresClientResource(ConfigurableResource):
    """This resource enables connecting to a Postgres cluster and issuing queries against that
    cluster.
    """

    host: str = Field(description="Postgres host")
    port: int = Field(default=5439, description="Postgres port")
    user: Optional[str] = Field(
        default=None, description="Username for Postgres connection"
    )
    password: Optional[str] = Field(
        default=None, description="Password for Postgres connection"
    )
    dbname: Optional[str] = Field(
        default=None,
        description=(
            "Name of the default database to use. After login, you can use USE DATABASE to change"
            " the database."
        ),
    )
    autocommit: Optional[bool] = Field(
        default=None, description="Whether to autocommit queries"
    )
    connect_timeout: int = Field(
        default=5,
        description="Timeout for connection to Postgres cluster. Defaults to 5 seconds.",
    )
    sslmode: str = Field(
        default="require",
        description=(
            "SSL mode to use. See the Postgres documentation for reference:"
            " https://www.postgresql.org/docs/current/libpq-ssl.html"
        ),
    )

    def get_client(self) -> PostgresClient:
        conn_args = {
            k: getattr(self, k, None)
            for k in (
                "host",
                "port",
                "user",
                "password",
                "dbname",
                "connect_timeout",
                "sslmode",
            )
            if getattr(self, k, None) is not None
        }

        return PostgresClient(conn_args, self.autocommit, get_dagster_logger())


class PGVectorClientResource(PostgresClientResource):
    def get_client(self) -> PGVectorClient:
        conn_args = {
            k: getattr(self, k, None)
            for k in (
                "host",
                "port",
                "user",
                "password",
                "dbname",
                "connect_timeout",
                "sslmode",
            )
            if getattr(self, k, None) is not None
        }

        return PGVectorClient(conn_args, self.autocommit, get_dagster_logger())
