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
    df = interests_clusters.slice(0, config.row_limit).sort(
        by=["cluster_label", "merged_cluster_label"], descending=False
    )

    fine_cluster_centroids = get_cluster_centroids(
        df.select("interests_embeddings").to_numpy(),
        df.select("cluster_label").to_numpy(),
    )[1:]  # Skip the firs one since it's for unclustered interests

    coarse_cluster_centroids = get_cluster_centroids(
        df.select("interests_embeddings").to_numpy(),
        df.select("merged_cluster_label").to_numpy(),
    )[1:]  # Skip the firs one since it's for unclustered interests

    fine_dissimilarity_ranking = dict(
        enumerate(get_maximally_dissimilar_embeddings(np.array(fine_cluster_centroids)))
    )

    coarse_dissimilarity_ranking = dict(
        enumerate(
            get_maximally_dissimilar_embeddings(np.array(coarse_cluster_centroids))
        )
    )

    result = df.with_columns(
        fine_dissimilarity_rank=pl.col("cluster_label").map_dict(
            fine_dissimilarity_ranking, default=-1
        ),
        coarse_dissimilarity_rank=pl.col("merged_cluster_label").map_dict(
            coarse_dissimilarity_ranking, default=-1
        ),
    )

    # Columns: interest_id, date, interests, interests_quirkiness,
    # interests_embeddings, cluster_label, merged_cluster_label,
    # fine_dissimilarity_rank, coarse_dissimilarity_rank
    return result
