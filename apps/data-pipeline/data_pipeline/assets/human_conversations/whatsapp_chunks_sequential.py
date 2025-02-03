import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import (
    API_STORAGE_DIRECTORY,
    DataProvider,
    get_environment,
)
from data_pipeline.partitions import (
    multi_phone_number_partitions_def,
)
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.resources.postgres_resource import PostgresResource
from data_pipeline.utils.agents.chunking_agent.chunking_agent import (
    ChunkDecision,
    ChunkingAgent,
)
from data_pipeline.utils.agents.save_agent_traces import save_agent_traces
from data_pipeline.utils.get_messaging_partners import get_messaging_partners


class WhatsappChunkingConfig(RowLimitConfig):
    row_limit: int | None = 100 if get_environment() == "LOCAL" else None
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
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
)
def whatsapp_chunks_sequential(
    context: AssetExecutionContext,
    config: WhatsappChunkingConfig,
    gpt4o: BaseLlmResource,
    postgres: PostgresResource,
) -> pl.DataFrame:
    llm = gpt4o

    messaging_partners = get_messaging_partners(
        postgres, context.partition_keys[0].split("|")
    )

    parsed_whatsapp_conversations = pl.read_json(
        API_STORAGE_DIRECTORY
        / messaging_partners.initiator_user_id
        / DataProvider.WHATSAPP_DESKTOP["path_prefix"]
        / "latest.json"  # TODO: change to snappy
    )

    df = (
        parsed_whatsapp_conversations.filter(
            pl.col("from").eq(messaging_partners.partner_name)
            | pl.col("to").eq(messaging_partners.partner_name)
        )
        .with_columns(
            datetime=pl.col("datetime").str.to_datetime(),
            # Initialize columns for processing
            chunk_id=pl.lit(None),
            sentiment=pl.lit(None),
        )
        .sort("datetime")
        .with_row_count("index")
        .slice(0, config.row_limit)
    )
    last_to_process_idx = 0
    last_log_time = time.time()

    def next_to_process(
        decision_payload: ChunkDecision | None = None
    ) -> tuple[str | None, bool]:
        nonlocal df, last_to_process_idx, last_log_time

        # Progress logging every 60 seconds
        current_time = time.time()
        if current_time - last_log_time >= 60:
            processed_rows = df.filter(pl.col("chunk_id").is_not_null()).height
            progress_percentage = (processed_rows / df.height) * 100
            context.log.info(
                f"Progress: {processed_rows}/{df.height} rows processed ({progress_percentage:.2f}%)"
            )
            last_log_time = current_time

        # Get the current max chunk_id or start with 0 if no chunks exist
        current_max_chunk = (
            df.filter(pl.col("chunk_id").is_not_null()).select("chunk_id").max().item()
            or 0
        )

        if decision_payload is None or decision_payload.decision == "NO_SPLIT":
            # Grow next input
            next_to_process = df.filter(
                pl.col("index") < last_to_process_idx + config.grow_by
            )
            # End condition
            if next_to_process["index"].max() == last_to_process_idx:
                df = df.with_columns(
                    pl.when(pl.col("chunk_id").is_null())
                    .then(pl.lit(current_max_chunk + 1))
                    .otherwise(pl.col("chunk_id"))
                    .alias("chunk_id")
                )
                return None, False
            else:
                last_to_process_idx = next_to_process["index"].max()
        elif decision_payload.decision == "SPLIT":
            # Update chunk_id and sentiment for rows up to the decision timestamp
            rows_to_update = pl.when(
                (pl.col("chunk_id").is_null())
                & (
                    pl.col("datetime")
                    < pl.lit(decision_payload.timestamp).str.to_datetime(
                        time_zone="UTC"
                    )
                )
            )
            df = df.with_columns(
                rows_to_update.then(pl.lit(current_max_chunk + 1))
                .otherwise(pl.col("chunk_id"))
                .alias("chunk_id"),
                rows_to_update.then(pl.lit(decision_payload.sentiment))
                .otherwise(pl.col("sentiment"))
                .alias("sentiment"),
            )

        next_to_process = df.filter(
            pl.col("chunk_id").is_null() & pl.col("index").le(last_to_process_idx)
        )

        over_max_size = next_to_process.height > config.max_chunk_size

        # Get all the messages with None chunk_id until the last_to_process_idx
        next_to_process_str = (
            next_to_process.select(
                pl.col("chunk_id"),
                messages_str=pl.concat_str(
                    [
                        pl.lit("From: "),
                        pl.col("from"),
                        pl.lit(", Date: "),
                        pl.col("datetime").dt.strftime("%Y-%m-%d %H:%M:%S"),
                        pl.lit(", Content: "),
                        pl.col("content"),
                    ]
                ),
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

    context.log.info(f"Total cost: ${sum((trace.cost or 0.0) for trace in traces)}")

    if config.save_traces:
        save_agent_traces(traces, context)

    return df
