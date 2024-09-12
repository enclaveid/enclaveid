import time
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.k8s import get_k8s_vllm_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info
from ...utils.search_history_utils import (
    get_full_history_sessions,
)


class InterestsConfig(RowLimitConfig):
    chunk_size: int = Field(
        default=10,
        description=(
            "Search history records are split into chunks of this size."
            " Chunking too many items can cause the LLM to give sub-par responses."
        ),
    )


enrichment_prompt_sequence = [
    (
        "Here is a list of my recent Google search activity."
        " What have I been doing? What were my goals?"
        " Be as specific as possible, using exact terms from the search activity."
    ),
    # Semicolons make is less prone to errors apparently
    (
        "Format the previous answer as a semicolon-separated array of strings delimited by square brackets."
        " Focus on the goal of the search activity in relation to the specific topic."
    ),
    dedent(
        """
        For each element in this list, determine if it's unique or quirky compared to what most people do online.
        Consider an activity unique or quirky if:
        - It's a specific or niche topic
        - Most people wouldn't typically engage in it online

        If an activity meets any of these criteria, consider it interesting.
        After your analysis, return a list of boolean flags (true/false) corresponding to each activity in the original list.
        Use 'true' for interesting activities and 'false' for others.
        """
    ),
]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(2),
    # retry_policy=spot_instance_retry_policy,
)
def interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    llama8b: Llama8bResource,
    full_takeout: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

    sessions_output = get_full_history_sessions(
        full_takeout=full_takeout,
        chunk_size=config.chunk_size,
        prompt_sequence=enrichment_prompt_sequence,
        local_llm=llama8b,
    )

    context.add_output_metadata(
        {
            "count_invalid_interests": sessions_output.count_invalid_interests,
            "count_invalid_uniqueness": sessions_output.count_invalid_uniqueness,
        }
    )

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns: date, interests, interests_uniqueness, raw_interests
    # NB: aggregate by date while the other assets are at date granularity
    return sessions_output.output_df
