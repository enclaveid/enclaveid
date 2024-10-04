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
from sklearn.cluster import AgglomerativeClustering

from data_pipeline.utils.clusters import (
    get_cluster_centroids,
    get_cluster_stats,
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
else:
    cuml = None
    cp = None
    HDBSCAN = None


class InterestsClustersConfig(RowLimitConfig):
    fine_min_cluster_size: int = Field(
        default=5,
        description="Minimum number of samples in an activity cluster to be considered an interest.",
    )
    coarse_recluster_threshold: float = Field(
        default=0.35,
        description="Cosine distance threshold for merging similar activities into broader categories. If None, coarse_n_clusters must be provided.",
    )
    coarse_n_clusters: int = Field(
        default=None,
        description="Number of clusters to merge into. If None, coarse_recluster_threshold must be provided.",
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

    # Calculate centroids of fine clusters
    fine_cluster_centroids = get_cluster_centroids(
        reduced_data_gpu.get(), fine_cluster_labels
    )

    merged_cluster_labels = AgglomerativeClustering(
        n_clusters=config.coarse_n_clusters,
        distance_threshold=config.coarse_recluster_threshold,
        **(
            {
                "metric": "cosine",
                "linkage": "average",
            }
            if config.coarse_recluster_threshold is not None
            else {
                "metric": "euclidean",
                "linkage": "ward",
            }
        ),
    ).fit_predict(list(fine_cluster_centroids.values()))

    remapped_merged_cluster_labels = np.array(
        [
            merged_cluster_labels[label] if label != -1 else label
            for label in fine_cluster_labels
        ]
    )

    context.add_output_metadata(
        get_cluster_stats(remapped_merged_cluster_labels, prefix="coarse_")
    )

    result = df.with_columns(
        cluster_label=pl.Series(fine_cluster_labels),
        merged_cluster_label=pl.Series(remapped_merged_cluster_labels),
    ).rename({"embeddings": "interests_embeddings"})

    context.log.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns: interest_id, date, interests, interests_quirkiness, interests_embeddings, cluster_label, merged_cluster_label
    return result
