import math
import os
from textwrap import dedent

import polars as pl
import psycopg
from dagster import AssetExecutionContext, asset
from pgvector.psycopg import register_vector
from pydantic import Field

from ..constants.custom_config import RowLimitConfig
from ..partitions import user_partitions_def
from ..resources.mistral_resource import MistralResource
from ..resources.postgres_resource import PGVectorClient, PGVectorClientResource
from ..utils.recent_history_utils import (
    ChunkedSessionOutput,
    get_daily_sessions,
    get_embeddings,
)

# TODO: Avoid auto-committing queries and bundle them as one transaction,
# where appropriate.

SUMMARY_PROMPT = dedent(
    """
    Analyze the provided list of Google search records to identify distinct topic groups. For each group, create a summary in the JSON format below. Ensure each summary includes:

    - `time_start`: The start time of the first search in the group.
    - `time_end`: The end time of the last search in the group.
    - `description`: A detailed account of the searches and site visits, enriched with inferred user intent and additional insights into the topic.
    - `interests`: A list of keywords representing the user's interests based on the searches.

    Each `description` should not only recap the searches but also offer a deeper understanding of what the user might be seeking or the broader context of their inquiries. Group searches based on thematic relevance and timing.

    Example of JSON output format:

    {
    "time_start": "HH:MM",
    "time_end": "HH:MM",
    "description": "Elaborate on what the user did and why, based on the search terms and visited pages.",
    "interests": ["keyword1", "keyword2"]
    }

    Here is a list of searches:
"""
)


class SessionsConfig(RowLimitConfig):
    chunk_size: int = Field(default=15, description="The size of each chunk.")
    ml_model_name: str = Field(
        default="mistral-tiny",
        description=(
            "The Mistral model to use. See the Mistral docs for a list of valid "
            "endpoints: https://docs.mistral.ai/platform/endpoints/"
        ),
    )
    rate_limit: float = Field(
        default=5.0,
        description=(
            "The maximum number of requests allowed per second. See the Mistral "
            "docs here: https://docs.mistral.ai/platform/pricing/"
        ),
    )


# TODO: Consider converting all these assets into a single graph-backed asset
# called recent_sessions.
@asset(partitions_def=user_partitions_def, io_manager_key="parquet_io_manager")
async def recent_sessions(
    context: AssetExecutionContext,
    config: SessionsConfig,
    mistral: MistralResource,
    recent_takeout: pl.DataFrame,
) -> pl.DataFrame:
    # Enforce the row_limit (if any) per day
    recent_takeout = recent_takeout.slice(0, config.row_limit)

    client = mistral.get_async_client()

    # Sort the data by time -- Polars might read data out-of-order
    recent_sessions = recent_takeout.sort("timestamp")

    # Split into multiple data frames (one per day). This is necessary to correctly
    # identify the data associated with each time entry.
    daily_dfs = recent_sessions.with_columns(
        date=pl.col("timestamp").dt.date()
    ).partition_by("date", as_dict=True, include_key=False)

    daily_outputs: list[ChunkedSessionOutput] = []
    for idx, (day, day_df) in enumerate(daily_dfs.items(), start=1):
        num_chunks = math.ceil(day_df.height / config.chunk_size)
        context.log.info(
            f"Processing {num_chunks} chunks for {day} ({idx} / {len(daily_dfs)})"
        )

        output = await get_daily_sessions(
            df=day_df,
            client=client,
            chunk_size=config.chunk_size,
            logger=context.log,
            day=day,
            prompt=SUMMARY_PROMPT,
            rate_limit=config.rate_limit,
            model=config.ml_model_name,
        )
        daily_outputs.append(output)

    context.add_output_metadata(
        {
            "num_sessions": sum(out.num_sessions for out in daily_outputs),
            "invalid_types": sum(out.invalid_types for out in daily_outputs),
            "invalid_keys": sum(out.invalid_keys for out in daily_outputs),
            "invalid_times": sum(out.invalid_times for out in daily_outputs),
            "invalid_sessions": sum(out.invalid_sessions for out in daily_outputs),
            "error_rate": round(
                sum(out.invalid_sessions for out in daily_outputs)
                / sum(out.num_sessions for out in daily_outputs),
                2,
            ),
        }
    )

    return pl.concat(out.output_df for out in daily_outputs)


# TODO: Consider encapsulating this logic in an IOManager and/or moving the binary
# copy logic into the PGVectorClient.
def upload_embeddings(
    context: AssetExecutionContext, client: PGVectorClient, df: pl.DataFrame
):
    context.log.info(f"Flushing existing rows for partition: {context.partition_key}")
    with client._get_conn() as conn, client._get_cursor(conn) as cur:
        cleanup_query = (
            f"DELETE FROM {context.asset_key.path[-1]} "
            f"WHERE user_id = '{context.partition_key}'"
        )
        context.log.debug(f"Executing query:\n{cleanup_query}")
        cur.execute(cleanup_query)  # type: ignore

    context.log.info(f"COPYing {len(df)} rows to Postgres...")
    col_list = (
        "user_id",
        "date",
        "time_start",
        "time_end",
        "description",
        "interests",
        "embedding",
    )

    df = df.select(col_list)

    copy_statement = (
        f"COPY {context.asset_key.path[-1]} "
        f"({', '.join(col_list)}) "
        "FROM STDIN "
        "WITH (FORMAT BINARY)"
    )

    # TODO: Optimization -- Using psycopg.AsyncConnection or asyncpg should speed this up
    num_rows = df.height
    with psycopg.connect(os.getenv("PSQL_URL", ""), autocommit=True) as conn:
        register_vector(conn)

        with conn.cursor().copy(copy_statement) as copy:  # type: ignore
            # Binary copy requires explicitly setting the types.
            # https://www.psycopg.org/psycopg3/docs/basic/copy.html#binary-copy
            copy.set_types(["text", "date", "time", "time", "text", "text[]", "vector"])

            for idx, r in enumerate(df.iter_rows(), start=1):
                copy.write_row(r)
                while conn.pgconn.flush() == 1:
                    pass

                if idx % 10 == 0 or idx == num_rows:
                    context.log.info(f"Finished copying {idx} / {num_rows} rows.")

    context.log.info("Finished COPY operation.")


class SessionEmbeddingsConfig(RowLimitConfig):
    batch_size: int = Field(
        default=100,
        description=(
            "Mistral allows passing a batch of multiple strings to the embeddings "
            "endpoint as a single request, maximising throughput. However, a "
            "single batch can only have a maximum  of 16,384 tokens. Reduce the "
            "batch size if the API returns a 'Too many tokens in batch.' error"
        ),
    )
    ml_model_name: str = Field(
        default="mistral-embed",
        description=(
            "The Mistral model to use. See the Mistral docs for a list of valid "
            "endpoints: https://docs.mistral.ai/platform/endpoints/"
        ),
    )
    rate_limit: float = Field(
        default=5.0,
        description=(
            "The maximum number of requests allowed per second. See the Mistral "
            "docs here: https://docs.mistral.ai/platform/pricing/"
        ),
    )


# TODO: Consider incorporate this logic inside recent_sessions.
@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
)
async def recent_session_embeddings(
    context: AssetExecutionContext,
    config: SessionEmbeddingsConfig,
    mistral: MistralResource,
    pgvector: PGVectorClientResource,
    recent_sessions: pl.DataFrame,
) -> pl.DataFrame:
    # Enforce row_limit (if any)
    recent_sessions = recent_sessions.slice(0, config.row_limit)

    num_chunks = math.ceil(len(recent_sessions) / config.batch_size)
    context.log.info(f"Getting embeddings for {num_chunks} chunks...")

    client = mistral.get_async_client()
    embeddings = await get_embeddings(
        texts=recent_sessions.get_column("description"),
        client=client,
        batch_size=config.batch_size,
        logger=context.log,
        rate_limit=config.rate_limit,
        model=config.ml_model_name,
    )

    recent_sessions = recent_sessions.with_columns(
        embedding=embeddings,
        user_id=pl.lit(context.partition_key),
    )

    upload_embeddings(context, pgvector.get_client(), recent_sessions)
    return recent_sessions


@asset(
    partitions_def=user_partitions_def,
    deps=[recent_session_embeddings],
)
def time_threshold(
    context: AssetExecutionContext,
    pgvector: PGVectorClientResource,
):
    client = pgvector.get_client()
    # Calculate the time and similarity thresholds for this user
    results = client.execute_query(
        query=f"""
        WITH LaggedSessions AS (
            SELECT
                date,
                time_start,
                time_end,
                LAG(time_end) OVER (ORDER BY date, time_start) AS prev_time_end
            FROM
                recent_session_embeddings
            WHERE
                user_id = '{context.partition_key}'
        ),

        TimeDifferences AS (
            SELECT
                EXTRACT('epoch' FROM time_start - prev_time_end) AS time_diff
            FROM
                LaggedSessions
            WHERE
                time_start > prev_time_end
        )

        SELECT
            percentile_cont(0.10) WITHIN GROUP (ORDER BY time_diff) AS time_interval_10th
        FROM
            TimeDifferences
        """,
        fetch_results=True,
    )

    if results is None or len(results) == 0:
        raise Exception(
            f"Could not determine the time_threshold for {context.partition_key}."
        )

    time_threshold = results[0][0]
    context.log.info(f"{time_threshold = }")
    return time_threshold


@asset(
    partitions_def=user_partitions_def,
    deps=[recent_session_embeddings],
)
def similarity_threshold(
    context: AssetExecutionContext,
    pgvector: PGVectorClientResource,
):
    client = pgvector.get_client()
    # Calculate the time and similarity thresholds for this user
    results = client.execute_query(
        query=f"""
        WITH CosineSimilarities AS (
            SELECT
                date,
                time_start,
                1 - (embedding <=> LAG(embedding) OVER (ORDER BY date, time_start)) AS cosine_similarity
            FROM
                recent_session_embeddings
            WHERE
                user_id = '{context.partition_key}'
        ),

        FilteredSimilarities AS (
            SELECT
                cosine_similarity
            FROM
                CosineSimilarities
            WHERE
                cosine_similarity IS NOT NULL
        )

        SELECT
            percentile_cont(0.90) WITHIN GROUP (ORDER BY cosine_similarity) AS embedding_similarity_90th
        FROM
            FilteredSimilarities""",
        fetch_results=True,
    )

    if results is None or len(results) == 0:
        raise Exception(
            f"Could not determine the similarity_threshold for {context.partition_key}."
        )

    similarity_threshold = results[0][0]
    context.log.info(f"{similarity_threshold = }")
    return similarity_threshold


@asset(
    partitions_def=user_partitions_def,
    deps=[recent_session_embeddings],
)
def recent_sessions_merged(
    context: AssetExecutionContext,
    pgvector: PGVectorClientResource,
    time_threshold,
    similarity_threshold,
):
    client = pgvector.get_client()

    context.log.info(
        f"Time threshold: {time_threshold:.2f} seconds. "
        f"Embedding similarity threshold: {similarity_threshold:.4f}"
    )

    # Create a copy of the sessions in the merged table (but first delete any
    # existing rows for this user)
    client.execute_query(
        f"DELETE FROM recent_sessions_merged where user_id = '{context.partition_key}'"
    )
    client.execute_query(
        query=f"""
        INSERT INTO recent_sessions_merged
        SELECT *
        FROM recent_session_embeddings
        WHERE user_id = '{context.partition_key}';
        """
    )

    # TODO: Explore implementing this logic in Polars instead. The problems with
    # the current logic are noted in Issue #4.
    #
    # --------------------------------------------------------------------------
    #
    # TODO: Explore recomputing a new description and embedding for the merged
    # session (or concatenating the description strings and finding the cluster
    # mean of the embeddings of all the sessions that will be merged) as an
    # alternative solution.
    candidates_to_merge = client.execute_query(
        query=f"""
        SELECT
            a.id,
            b.id
        FROM
            recent_sessions_merged a
        JOIN
            recent_sessions_merged b
            ON
                a.user_id = '{context.partition_key}'
                AND a.user_id = b.user_id
                AND a.id != b.id
                AND (
                    b.date > a.date
                    OR (a.date = b.date AND b.time_start >= a.time_end)
                )
        WHERE
            EXTRACT(
                'epoch' FROM (
                    (b.date || ' ' || b.time_start)::timestamp
                    - (a.date || ' ' || a.time_end)::timestamp
                )
            ) <= {time_threshold}
            AND
            1 - (a.embedding <=> b.embedding) >= {similarity_threshold}""",
        fetch_results=True,
    )

    msg = "\n".join(str(pair) for pair in candidates_to_merge)  # type: ignore
    context.log.info(f"Merging sessions:\n{msg}")

    for a, b in candidates_to_merge:  # type: ignore
        # Update time_end of document a with the maximum time_end of both sessions
        client.execute_query(
            f"""
            UPDATE recent_sessions_merged
            SET time_end = (
                SELECT
                    GREATEST(max_a.time_end, max_b.time_end)
                FROM
                    (SELECT time_end FROM recent_sessions_merged WHERE id = {a}) as max_a,
                    (SELECT time_end FROM recent_sessions_merged WHERE id = {b}) as max_b
            )
            WHERE id = {a}
            """
        )

        # Update time_start of document a with the minimum time_start of both sessions
        client.execute_query(
            f"""
            UPDATE recent_sessions_merged
            SET time_start = (
                SELECT
                    LEAST(min_a.time_start, min_b.time_start)
                FROM
                    (SELECT time_start FROM recent_sessions_merged WHERE id = {a}) as min_a,
                    (SELECT time_start FROM recent_sessions_merged WHERE id = {b}) as min_b
            )
            WHERE id = {a}
            """
        )
        # Delete the duplicate session
        client.execute_query(f"DELETE FROM recent_sessions_merged WHERE id = {b}")


# TODO: The logic is quite similar to what HDBSCAN does, we should consider using it instead.
@asset(
    partitions_def=user_partitions_def,
    deps=[recent_sessions_merged],
)
def recent_sessions_graph(
    context: AssetExecutionContext,
    pgvector: PGVectorClientResource,
    similarity_threshold,
):
    client = pgvector.get_client()

    # Cleanup existing data for this partition (i.e., user)
    client.execute_query(
        f"DELETE FROM recent_sessions_graph where user_id = '{context.partition_key}'"
    )

    # Update the graph with the edges for this partition (i.e., user)
    client.execute_query(
        f"""
        WITH DocumentPairs AS (
            SELECT
                a.user_id,
                a.id AS doc_id,
                b.id AS compared_doc_id,
                1 - (a.embedding <=> b.embedding) AS similarity,
                a.date AS doc_date,
                b.date AS compared_doc_date,
                a.time_end AS doc_time_end,
                b.time_start AS compared_doc_time_start
            FROM
                recent_sessions_merged a
            JOIN
                recent_sessions_merged b
                ON
                    a.user_id = '{context.partition_key}'
                    AND a.user_id = b.user_id
                    AND a.id != b.id
                    AND (
                        b.date > a.date
                        OR (a.date = b.date AND b.time_start >= a.time_end)
                    )
        ),

        RankedPairs AS (
            SELECT
                *,
                ROW_NUMBER() OVER(
                    PARTITION BY user_id, doc_id
                    ORDER BY similarity DESC
                ) AS rank
            FROM
                DocumentPairs
        ),

        FilteredPairs1 as (
            SELECT
                user_id,
                doc_id,
                compared_doc_id,
                similarity
            FROM
                RankedPairs
            WHERE
                rank = 1
                AND similarity > {similarity_threshold}
        )

        INSERT INTO recent_sessions_graph (user_id, parent_id, child_id, weight)

        SELECT
            user_id,
            doc_id,
            compared_doc_id,
            1 - similarity as distance
        FROM
            FilteredPairs1
        """
    )
