from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.capabilities import is_rapids_image
from data_pipeline.utils.clusters import get_cluster_centroids
from data_pipeline.utils.get_maximally_dissimilar_embeddings import (
    get_maximally_dissimilar_embeddings,
)

if is_rapids_image() or TYPE_CHECKING:
    import cupy as cp
else:
    cp = None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_clusters": AssetIn(key=["interests_clusters"])},
    op_tags=get_k8s_rapids_config(),
)
def dissimilar_funny_interests_clusters(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
    fine_cluster_centroids = get_cluster_centroids(
        interests_clusters.select("interests_embeddings").to_numpy(),
        interests_clusters.select("cluster_label").to_numpy(),
    )

    coarse_cluster_centroids = get_cluster_centroids(
        interests_clusters.select("interests_embeddings").to_numpy(),
        interests_clusters.select("merged_cluster_label").to_numpy(),
    )

    fine_dissimilarity_ranking = get_maximally_dissimilar_embeddings(
        np.array(fine_cluster_centroids)
    )

    coarse_dissimilarity_ranking = get_maximally_dissimilar_embeddings(
        np.array(coarse_cluster_centroids)
    )

    result = interests_clusters.with_columns(
        fine_dissimilarity_rank=pl.Series(fine_dissimilarity_ranking),
        coarse_dissimilarity_rank=pl.Series(coarse_dissimilarity_ranking),
    )

    # Columns: interest_id, date, interests, interests_quirkiness,
    # interests_embeddings, cluster_label, merged_cluster_label,
    # fine_dissimilarity_rank, coarse_dissimilarity_rank
    return result
