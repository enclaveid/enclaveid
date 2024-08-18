import time
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.utils.costs import get_gpu_runtime_cost

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import get_k8s_rapids_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info, is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cuml
    import cupy as cp
    from cuml.cluster.hdbscan import HDBSCAN


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_embeddings": AssetIn(key=["interests_embeddings"])},
    op_tags=get_k8s_rapids_config(1),
)
def interests_clusters(
    context: AssetExecutionContext,
    config: RowLimitConfig,
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

    clusterer = HDBSCAN(
        min_cluster_size=10,
        gen_min_span_tree=True,
        metric="euclidean",
        # By specifying an epsilon we can coalesce similar clusters but we rather keep
        # them separate until after the bipartite matching stage
        # cluster_selection_epsilon=0.15,
    )
    cluster_labels = clusterer.fit_predict(reduced_data_gpu.astype(np.float64).get())

    cluster_stats = np.unique(cluster_labels, return_counts=True)

    context.add_output_metadata(
        {
            "clusters_count": len(cluster_stats[0]),
            "noise_count": int(cluster_stats[1][0]) if -1 in cluster_stats[0] else 0,
        }
    )

    # Remove the embeddings to save space
    result = df.with_columns(cluster_label=pl.Series(cluster_labels)).drop("embeddings")

    context.log.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    return result
