import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_messaging_partner_name import (
    MIN_HUMAN_CONVERSATION_CHUNK_SIZE,
)


class WhatsappConversationRechunkedConfig(Config):
    min_chunk_size: int = Field(
        default=MIN_HUMAN_CONVERSATION_CHUNK_SIZE,
        description="The minimum number of messages in a chunk",
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_chunks": AssetIn(
            key=["whatsapp_conversation_chunks"],
        ),
    },
)
def whatsapp_conversation_rechunked(
    context: AssetExecutionContext,
    config: WhatsappConversationRechunkedConfig,
    whatsapp_conversation_chunks: pl.DataFrame,
) -> pl.DataFrame:
    """
    Standardize chunk outputs from the LLM.

    Columns:
    - start_dt: Start datetime of the chunk
    - end_dt: End datetime of the chunk
    - decisions: List of decisions merged during this rechunking process
    - messages_struct: List of messages in the chunk (from, to, date, time, content)
    """
    df = whatsapp_conversation_chunks.filter(
        pl.col("decision").is_not_null()
    ).with_columns(
        # Cast time strings to Time type
        chunks=pl.col("chunks").list.eval(
            pl.struct(
                start_time=pl.element().struct.field("start_time").str.to_time(),
                end_time=pl.element().struct.field("end_time").str.to_time(),
            )
        ),
    )

    # Filter for rows where decision is CHUNK and explode them
    chunked_conversations = (
        df.filter(pl.col("decision").eq("CHUNK"))
        .explode("chunks")
        .explode("messages_struct")
        .with_columns(
            pl.col("messages_struct")
            .struct.field("time")
            .str.to_time()
            .ge(pl.col("chunks").struct.field("start_time"))
            .alias("time_in_chunk_start"),
            pl.col("messages_struct")
            .struct.field("time")
            .str.to_time()
            .le(pl.col("chunks").struct.field("end_time"))
            .alias("time_in_chunk_end"),
        )
        .filter(pl.col("time_in_chunk_start") & pl.col("time_in_chunk_end"))
        .group_by(pl.all().exclude("messages_struct"), maintain_order=True)
        .all()
        .select("date", "decision", "chunks", "messages_struct")
    )

    context.log.info(f"Computed {len(chunked_conversations)} chunked conversations")

    # Standardize chunks column for non-chunked conversations
    non_chunked_conversations = (
        df.filter(pl.col("decision").ne("CHUNK"))
        .with_columns(
            chunks=pl.struct(
                start_time=pl.col("messages_struct")
                .list.eval(pl.element().struct.field("time").str.to_time().min())
                .list.first(),
                end_time=pl.col("messages_struct")
                .list.eval(pl.element().struct.field("time").str.to_time().max())
                .list.first(),
            )
        )
        # Sort the columns of the chunked conversations to match the non-chunked conversations
        .select(chunked_conversations.columns)
    )

    context.log.info(
        f"Computed {len(non_chunked_conversations)} non-chunked conversations"
    )

    combined_df = (
        pl.concat([non_chunked_conversations, chunked_conversations])
        .with_columns(
            # Remap NO_CHUNK to CHUNK
            pl.col("decision").map_elements(lambda x: "CHUNK" if x == "NO_CHUNK" else x)
        )
        .with_columns(
            # Add time range columns for rollup
            start_dt=pl.col("date").dt.combine(
                pl.col("chunks").struct.field("start_time")
            ),
            end_dt=pl.col("date").dt.combine(pl.col("chunks").struct.field("end_time")),
        )
        .sort("start_dt")
        .drop(["date", "chunks"])
    )

    context.log.info(f"Computed {len(combined_df)} combined conversations")

    # ---- Merge INCONCLUSIVE and size < min_chunk_size rows with adjacent CHUNK and size >= min_chunk_size rows ----

    # Mark good rows; all others get null for chunk_id
    df_with_chunk_id = combined_df.with_columns(
        pl.when(
            pl.col("decision").eq("CHUNK")
            & pl.col("messages_struct").list.len().ge(config.min_chunk_size)
        )
        .then(pl.arange(0, pl.count(), 1))
        .otherwise(None)
        .alias("chunk_id")
    )

    # Forward-fill and backward-fill chunk_id so the merged rows get the chunk_id of the first good row above and below them
    result_df = (
        df_with_chunk_id.with_columns(
            pl.col("chunk_id").fill_null(strategy="backward"),
        )
        .with_columns(
            pl.col("chunk_id").fill_null(strategy="forward"),
        )
        .group_by("chunk_id")
        .agg(
            [
                pl.col("start_dt").min(),
                pl.col("end_dt").max(),
                pl.col("decision").alias("decisions"),
                pl.col("messages_struct").flatten(),
            ]
        )
        .sort("start_dt")
        .with_columns(
            pl.col("messages_struct").list.eval(
                pl.element().sort_by(
                    pl.element().struct.field("date"),
                    pl.element().struct.field("time"),
                )
            )
        )
    )

    return result_df
