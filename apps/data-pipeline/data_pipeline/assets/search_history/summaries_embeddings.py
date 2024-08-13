import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.resources.cost_tracker_resource import CostTrackerResource
from data_pipeline.resources.llm_inference.sentence_transformer_resource import (
    SentenceTransformerResource,
)
from data_pipeline.utils.capabilities import gpu_info
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import k8s_vllm_config
from ...partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "cluster_summaries": AssetIn(key=["cluster_summaries"]),
    },
    op_tags=k8s_vllm_config,
)
def summaries_embeddings(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    sentence_transformer: SentenceTransformerResource,
    cost_tracker: CostTrackerResource,
    cluster_summaries: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    df = cluster_summaries.slice(0, config.row_limit)

    context.log.info("Computing embeddings...")
    result = df.with_columns(
        summary_embedding=pl.col("cluster_summary").map_batches(
            sentence_transformer.get_embeddings
        ),
        items_embedding=pl.col("cluster_items").map_batches(
            sentence_transformer.get_embeddings
        ),
    )

    cost_tracker.log_cost(get_gpu_runtime_cost(start_time), context)

    return result
