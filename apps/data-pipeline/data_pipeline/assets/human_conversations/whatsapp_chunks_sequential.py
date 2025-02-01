import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.agents.chunking_agent.chunking_agent import (
    ChunkDecision,
    ChunkingAgent,
)
from data_pipeline.utils.agents.save_agent_traces import save_agent_traces
from data_pipeline.utils.get_messaging_partners import get_messaging_partners


class WhatsappChunkingConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None
    max_chunk_size: int = Field(
        default=100, description="Max chunk size in number of messages"
    )
    grow_by: int = Field(
        default=20, description="Number of messages to grow the chunk by"
    )
    save_traces: bool = Field(
        default=True, description="Whether to save the agent traces"
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "parsed_whatsapp_conversations": AssetIn(
            key=["parsed_whatsapp_conversations"],
        ),
    },
)
def whatsapp_chunks_sequential(
    context: AssetExecutionContext,
    config: WhatsappChunkingConfig,
    gpt4o: BaseLlmResource,
    parsed_whatsapp_conversations: pl.DataFrame,
) -> pl.DataFrame:
    llm = gpt4o

    messaging_partners = get_messaging_partners()
    df = (
        parsed_whatsapp_conversations.filter(
            pl.col("from").eq(messaging_partners.partner)
            | pl.col("to").eq(messaging_partners.partner)
        )
        .with_columns(pl.lit(None).alias("chunk_id"))
        .sort("datetime")
        .with_row_count("index")
    )
    last_to_process_idx = 0

    def next_to_process(
        decision_payload: ChunkDecision | None = None
    ) -> tuple[str | None, bool]:
        nonlocal df, last_to_process_idx

        if decision_payload is None or decision_payload.decision == "NO_SPLIT":
            # Grow next input
            next_to_process = df.filter(
                pl.col("index") < last_to_process_idx + config.grow_by
            )
            last_to_process_idx = next_to_process["index"].max()
        elif decision_payload.decision == "SPLIT":
            # Get the current max chunk_id or start with 0 if no chunks exist
            current_max_chunk = (
                df.filter(pl.col("chunk_id").is_not_null())
                .select("chunk_id")
                .max()
                .item()
                or 0
            )

            # Update chunk_id for rows up to the decision timestamp
            df = df.with_columns(
                pl.when(
                    (pl.col("chunk_id").is_null())
                    & (
                        pl.col("datetime")
                        < pl.lit(decision_payload.timestamp).str.to_datetime()
                    )
                )
                .then(pl.lit(current_max_chunk + 1))
                .otherwise(pl.col("chunk_id"))
                .alias("chunk_id")
            )

            # Set last_to_process_idx to the index of the last row in the new chunk
            last_to_process_idx = df.filter(
                pl.col("chunk_id") == current_max_chunk + 1
            )["index"].max()

        next_to_process = df.filter(
            pl.col("chunk_id").is_null() & pl.col("index") <= last_to_process_idx
        )

        over_max_size = next_to_process.height > config.max_chunk_size

        # Get all the messages with None chunk_id until the last_to_process_idx
        next_to_process_str = (
            next_to_process.select(
                messages_str=pl.concat_str(
                    [
                        pl.lit("From: "),
                        pl.col("from"),
                        pl.lit(", Date: "),
                        pl.col("datetime").dt.strftime("%Y-%m-%d %H:%M:%S"),
                        pl.lit(", Content: "),
                        pl.col("content"),
                    ]
                )
            )
            .group_by("chunk_id")
            .agg(pl.col("messages_str").str.join("\n").alias("messages_str"))
            .get_column("messages_str")
            .item()
        )

        return next_to_process_str, over_max_size

    traces = ChunkingAgent(llm.llm_config).chunk_messages(
        next_to_process,
    )

    if config.save_traces:
        save_agent_traces(traces, context)

    return df
