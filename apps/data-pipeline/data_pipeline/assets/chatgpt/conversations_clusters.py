from textwrap import dedent
from typing import Optional

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.capabilities import is_rapids_image
from data_pipeline.utils.clusters import get_cluster_centroids, get_cluster_stats

IS_RAPIDS = is_rapids_image()

if IS_RAPIDS:
    import cupy as xp
    from cuml import UMAP
    from cuml.cluster import AgglomerativeClustering
    from cuml.cluster.hdbscan import HDBSCAN
else:
    import numpy as xp
    from sklearn.cluster import HDBSCAN, AgglomerativeClustering
    from umap import UMAP


class ConversationsClustersConfig(Config):
    fine_min_cluster_size: int = Field(
        default=2,
        description="Minimum number of samples in an activity cluster to be considered an interest.",
    )
    coarse_recluster_threshold: Optional[float] = Field(
        default=0.3,
        description=dedent(
            """
            Cosine distance threshold for merging similar activities into broader categories.
            If None, coarse_n_clusters must be provided.
            Cosine 0.3 is a good default for broad categorization. (technology, entertainment, etc.)
            """
        ).strip(),
    )
    coarse_n_clusters: Optional[int] = Field(
        default=100,
        description="Number of clusters to merge into. If None, coarse_recluster_threshold must be provided.",
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "conversation_embeddings": AssetIn(
            key=["conversation_embeddings"],
        ),
    },
    op_tags=get_k8s_rapids_config(),
)
def conversations_clusters(
    context: AssetExecutionContext,
    config: ConversationsClustersConfig,
    conversation_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    df = conversation_embeddings.filter(pl.col("summary_embedding").is_not_null())

    # Convert the embeddings column to a 2D numpy array
    summaries_embeddings = xp.stack(df["summary_embedding"].to_list())

    # Reduce the embeddings dimensions
    umap_model = UMAP(n_neighbors=15, n_components=100, min_dist=0.1, metric="cosine")
    reduced_data = umap_model.fit_transform(summaries_embeddings)

    # Move data to cpu if on gpu
    if IS_RAPIDS:
        reduced_data = reduced_data.astype(xp.float64).get()
    else:
        reduced_data = reduced_data.astype(xp.float64)

    # Clustering for single interests
    fine_cluster_labels = HDBSCAN(
        min_cluster_size=config.fine_min_cluster_size,
        # gen_min_span_tree=True,
        metric="euclidean",
    ).fit_predict(reduced_data)

    context.log.info(
        f"Fine clusters: {xp.unique(fine_cluster_labels, return_counts=True)}"
    )

    # Calculate centroids of fine clusters
    fine_cluster_centroids = get_cluster_centroids(reduced_data, fine_cluster_labels)

    agglomerative_clustering_params = (
        {
            "n_clusters": None,
            "distance_threshold": config.coarse_recluster_threshold,
            "metric": "cosine",
            "linkage": "average",
        }
        if config.coarse_recluster_threshold is not None
        else {
            "n_clusters": config.coarse_n_clusters,
            "distance_threshold": None,
            "metric": "euclidean",
            "linkage": "ward",
        }
    )

    coarse_cluster_labels = AgglomerativeClustering(
        **agglomerative_clustering_params
    ).fit_predict(list(fine_cluster_centroids.values()))  # type: ignore

    context.log.info(get_cluster_stats(coarse_cluster_labels, prefix="coarse_"))

    return df.with_columns(
        fine_cluster_label=fine_cluster_labels,
        coarse_cluster_label=coarse_cluster_labels,  # type: ignore
    )
