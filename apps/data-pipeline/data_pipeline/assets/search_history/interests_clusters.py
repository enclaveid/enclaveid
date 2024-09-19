import time
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.utils.clusters import get_cluster_stats
from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import get_k8s_rapids_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info, is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cuml
    import cupy as cp
    from cuml.cluster.hdbscan import HDBSCAN
else:
    cuml = None
    cp = None
    HDBSCAN = None


class InterestsClustersConfig(RowLimitConfig):
    fine_min_cluster_size: int = Field(
        default=5,
        description="Minimum number of samples in an activity cluster to be considered an interest.",
    )
    # With these default values we are expeciting ~100 clusters
    coarse_min_cluster_size: int = Field(
        default=10,
        description="Minimum number of samples in an activity cluster to be considered a category. Should be equal or larger than fine_min_cluster_size.",
    )
    coarse_cluster_selection_epsilon: float = Field(
        default=0.3,
        description="Epsilon value for merging similar activities into broader categories.",
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_embeddings": AssetIn(key=["interests_embeddings"])},
    op_tags=get_k8s_rapids_config(),
    # retry_policy=spot_instance_retry_policy,
)
def interests_clusters(
    context: AssetExecutionContext,
    config: InterestsClustersConfig,
    interests_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    # Apply the row limit (if any)
    df = interests_embeddings.slice(0, config.row_limit)

    # Convert the embeddings to a CuPy array
    embeddings_gpu = cp.asarray(df["embeddings"].to_numpy())

    # Reduce the embeddings dimensions
    umap_model = cuml.UMAP(
        n_neighbors=15, n_components=100, min_dist=0.1, metric="cosine"
    )
    reduced_data_gpu = umap_model.fit_transform(embeddings_gpu)

    # Clustering for single interests
    fine_cluster_labels = HDBSCAN(
        min_cluster_size=config.fine_min_cluster_size,
        gen_min_span_tree=True,
        metric="euclidean",
    ).fit_predict(reduced_data_gpu.astype(np.float64).get())

    context.add_output_metadata(get_cluster_stats(fine_cluster_labels, prefix="fine_"))

    # See: https://hdbscan.readthedocs.io/en/latest/how_to_use_epsilon.html
    coarse_cluster_labels = HDBSCAN(
        min_cluster_size=config.coarse_min_cluster_size,
        gen_min_span_tree=True,
        metric="euclidean",
        cluster_selection_epsilon=config.coarse_cluster_selection_epsilon,
    ).fit_predict(reduced_data_gpu)

    context.add_output_metadata(
        get_cluster_stats(coarse_cluster_labels, prefix="coarse_")
    )

    result = df.with_columns(
        cluster_label=pl.Series(fine_cluster_labels),
        merged_cluster_label=pl.Series(coarse_cluster_labels),
    ).rename({"embeddings": "interests_embeddings"})

    context.log.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns: interest_id, date, interests, interests_quirkiness, interests_embeddings, cluster_label, merged_cluster_label
    return result
