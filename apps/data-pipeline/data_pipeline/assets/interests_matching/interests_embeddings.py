import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.k8s import get_k8s_vllm_config
from ...partitions import user_partitions_def
from ...resources.nvembed_resource import NVEmbedResource
from ...utils.capabilities import gpu_info


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests": AssetIn(key=["interests"])},
    op_tags=get_k8s_vllm_config(),
    # retry_policy=spot_instance_retry_policy,
)
def interests_embeddings(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    nvembed: NVEmbedResource,
    interests: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    df = (
        # Enforce row_limit (if any)
        interests.slice(0, config.row_limit)
        .select("date", "interests")
        # Explode the interests so we get the embeddings for each individual interest
        .explode("interests")
        .drop_nulls()
        .with_row_index("interest_id")
    )

    context.log.info("Computing embeddings")
    result = df.with_columns(
        embeddings=pl.col("interests").map_batches(nvembed.get_embeddings),
    )

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns: interest_id, date, interests, embeddings
    return result
