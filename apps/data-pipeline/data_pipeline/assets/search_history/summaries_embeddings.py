import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.resources.sentence_transfomer_resource import (
    SentenceTransformerResource,
)
from data_pipeline.utils.capabilities import gpu_info
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import get_k8s_vllm_config
from ...partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "cluster_summaries": AssetIn(key=["cluster_summaries"]),
    },
    op_tags=get_k8s_vllm_config(),
    # retry_policy=spot_instance_retry_policy,
)
def summaries_embeddings(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    embedding_model: SentenceTransformerResource,
    cluster_summaries: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    df = cluster_summaries.slice(0, config.row_limit)

    context.log.info("Computing embeddings...")
    result = df.with_columns(
        summary_embedding=pl.col("cluster_summary").map_batches(
            embedding_model.get_embeddings
        ),
        items_embedding=pl.col("cluster_items").map_batches(
            embedding_model.get_embeddings
        ),
    )

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    return result
