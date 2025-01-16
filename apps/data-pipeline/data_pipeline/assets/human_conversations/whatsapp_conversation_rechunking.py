import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_chunks": AssetIn(
            key=["whatsapp_conversation_chunks"],
        ),
    },
)
def whatsapp_conversation_rechunking(
    context: AssetExecutionContext,
    config: Config,
    whatsapp_conversation_chunks: pl.DataFrame,
) -> pl.DataFrame:
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
        .drop(["date", "chunks"])
    )

    context.log.info(f"Computed {len(combined_df)} combined conversations")

    # Incorporate INCONCLUSIVE chunks with next row until CHUNK
    result_df = (
        combined_df.sort(["start_dt"])
        .with_columns(
            # Create a group ID that changes when we hit a CHUNK decision
            group_id=pl.col("decision").eq("CHUNK").cum_sum()
        )
        .group_by("group_id")
        .agg(
            messages_struct=pl.col("messages_struct"),
            decision=pl.col("decision").last(),  # Take the last decision (CHUNK)
            start_dt=pl.col("start_dt").min(),  # Take earliest start time
            end_dt=pl.col("end_dt").max(),  # Take latest end time
        )
        .drop("group_id")
    )

    context.log.info(f"Computed {len(result_df)} final conversations")

    # Combine both dataframes
    return result_df
