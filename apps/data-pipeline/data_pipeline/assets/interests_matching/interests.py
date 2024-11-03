from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.consts import get_environment
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
            "Search history records are split into chunks of this size. "
            "Chunking too many items can cause the LLM to give sub-par responses."
        ),
    )


enrichment_prompt_sequence = [
    dedent(
        """
        Here is a list of my recent Google search activity.
        What have I been doing?

        Consider the following:
        - Be as specific as possible, but without repeating the searches verbatim.
        - Condense similar activities in same activity where appropriate, while maintaining specificity.
        - Include details from your knowledge in the strings to clarify possible ambiguities.

        Most importantly, do not provide a generic description where details are available.
        """
    ),
    # Focus on the goal of the search activity in relation to the specific topic.
    dedent(
        """
        Format your answers in a list like this, including the time range for each group of activities:
        [
            "hh:mm - hh:mm, group 1 description",
            "hh:mm - hh:mm, group 2 description",
            ...
        ]
        """
    ),
]

TEST_ROW_LIMIT = 1000 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(),
    # retry_policy=spot_instance_retry_policy,
)
def interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    gemini_flash: BaseLlmResource,
    full_takeout: pl.DataFrame,
) -> pl.DataFrame:
    context.log.info(gpu_info())

    full_takeout = full_takeout.slice(0, TEST_ROW_LIMIT)

    sessions_output = get_full_history_sessions(
        full_takeout=full_takeout.sort("timestamp"),
        chunk_size=config.chunk_size,
        prompt_sequence=enrichment_prompt_sequence,
        llm_resource=gemini_flash,
    )

    context.add_output_metadata(
        {
            "count_invalid_interests": sessions_output.count_invalid_interests,
        }
    )

    # Columns: date, interests, raw_interests, raw_results
    # NB: aggregate by date while the other assets are at date granularity
    return sessions_output.output_df
