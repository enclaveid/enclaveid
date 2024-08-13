import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.cost_tracker_resource import CostTrackerResource
from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.k8s import k8s_vllm_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info
from ...utils.search_history_utils import (
    get_full_history_sessions,
)


class InterestsConfig(RowLimitConfig):
    ml_model_name: str = Field(
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        description=(
            "The Hugging Face model to use as the LLM. See the vLLMs docs for a "
            "list of the support models:\n"
            "https://docs.vllm.ai/en/latest/models/supported_models.html"
        ),
    )

    chunk_size: int = Field(
        default=10,
        description=(
            "Split the raw history into chunks of this size. We allow vLLM to "
            "determine the ideal batch size by itsef, so this has no impact on "
            "runtime but it still determines how many records are shown to the "
            "LLM at one time. Having too many records can cause the LLM to give "
            "sub-par responses."
        ),
    )


enrichment_prompt_sequence = [
    (
        "Here is a list of my recent Google search activity."
        " What have I been doing? What were my goals?"
        " Be as specific as possible, using exact terms from the search activity."
    ),
    (
        "Format the previous answer as a semicolon-separated array of strings delimited by square brackets."
        " Focus on the goal of the search activity in relation to the specific topic."
    ),
]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    op_tags=k8s_vllm_config,
)
def interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    llama8b: Llama8bResource,
    cost_tracker: CostTrackerResource,
    full_takeout: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

    sessions_output = get_full_history_sessions(
        full_takeout=full_takeout,
        chunk_size=config.chunk_size,
        first_instruction=enrichment_prompt_sequence[0],
        second_instruction=enrichment_prompt_sequence[1],
        llama8b=llama8b,
    )

    context.add_output_metadata(
        {"count_invalid_responses": sessions_output.count_invalid_responses}
    )

    cost_tracker.log_cost(get_gpu_runtime_cost(start_time), context)

    return sessions_output.output_df
