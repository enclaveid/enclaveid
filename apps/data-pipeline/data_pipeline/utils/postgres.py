import polars as pl
import psycopg
from dagster import get_dagster_logger
from psycopg import sql
from sqlalchemy import make_url


def conn_string_to_conn_args(conn_string: str):
    url = make_url(conn_string)
    return {
        "host": url.host,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "dbname": url.database,
    }


# TODO: Handle conflicts
def insert_dataframe_to_table(
    df: pl.DataFrame, conn: psycopg.Connection, table_name: str
) -> list:
    # Convert Polars DataFrame to list of tuples
    data = df.to_numpy().tolist()
    columns = df.columns

    # Create SQL query for inserting data with conflict handling
    column_names = sql.SQL(", ").join(map(sql.Identifier, columns))
    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))

    logger = get_dagster_logger()
    logger.info(f"Inserting {len(data)} rows of {column_names} into {table_name}")

    insert_query = sql.SQL(
        """
        INSERT INTO {table} ({columns})
        VALUES ({values})
        RETURNING id
    """
    ).format(
        table=sql.Identifier(table_name),
        columns=column_names,
        values=placeholders,
    )

    # Execute the query and fetch the inserted IDs
    with conn.cursor() as cur:
        cur.executemany(insert_query, data)
        inserted_ids = [row[0] for row in cur.fetchall()]

    return inserted_ids
