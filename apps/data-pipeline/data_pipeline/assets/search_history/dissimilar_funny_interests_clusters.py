from typing import TYPE_CHECKING
from data_pipeline.utils.capabilities import is_rapids_image
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_maximally_dissimilar_embeddings import (
    get_maximally_dissimilar_embeddings,
)

import numpy as np

if is_rapids_image() or TYPE_CHECKING:
    import cupy as cp
else:
    cp = None


class DissimilarFunnyInterestsConfig(RowLimitConfig):
    max_count: int = Field(
        default=1000,
        description="The number of maximally dissimilar funny interests to return.",
    )

def get_cluster_centroids(embeddings_gpu: cp.ndarray, cluster_labels: np.ndarray):



@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_clusters": AssetIn(key=["interests_clusters"])},
    op_tags=get_k8s_rapids_config(1),
)
def dissimilar_funny_interests_clusters(
    context: AssetExecutionContext,
    config: DissimilarFunnyInterestsConfig,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
    cluster_centroids = get_cluster_centroids(
        interests_clusters.select("embeddings").to_numpy(),
        interests_clusters.select("cluster_label").to_numpy(),
    )

    merged_cluster_centroids = get_cluster_centroids(
        interests_clusters.select("embeddings").to_numpy(),
        interests_clusters.select("merged_cluster_label").to_numpy(),
    )

    df = interests_clusters.slice(0, config.row_limit).filter(
        pl.col("interests_quirkiness").eq(True)
    )

    if df.is_empty():
        return pl.DataFrame()

    indices = get_maximally_dissimilar_embeddings(
        df.select("embeddings").to_numpy(), config.max_count
    )

    result = df.with_columns(maximally_dissimilar=pl.arange(0, len(df)).is_in(indices))

    # Columns: interest_id, date, interests, interests_quirkiness, embeddings, maximally_dissimilar
    return result
