import time
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource

from ...constants.k8s import get_k8s_vllm_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info
from ...utils.search_history_utils import (
    get_full_history_sessions,
)


class InterestsConfig(RowLimitConfig):
    chunk_size: int = Field(
        default=5,
        description=(
            "Search history records are split into chunks of this size."
            " Chunking too many items can cause the LLM to give sub-par responses."
        ),
    )


enrichment_prompt_sequence = [
    dedent(
        """
        Here is a list of my recent Google search activity.
        What have I been doing? What were my goals?
        Be as specific as possible, using exact terms from the search activity.
    """
    ),
    dedent(
        """
        Format your answers in an array of strings like this:
        {
          "activities": ["activity1", "activity2", ...],
        }
        Focus on the goal of the search activity in relation to the specific topic.
        Condense similar activities in same activity where appropriate, while maintaining specificity.
        Include details from your knowledge in the strings to clarify possible ambiguities.
    """
    ),
]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(),
    # retry_policy=spot_instance_retry_policy,
)
def interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    llama8b: BaseLlmResource,
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
        }
    )

    # Columns: date, interests, raw_interests, raw_results
    # NB: aggregate by date while the other assets are at date granularity
    return sessions_output.output_df
