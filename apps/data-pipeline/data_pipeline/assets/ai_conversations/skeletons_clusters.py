import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field
from sklearn.cluster import AgglomerativeClustering

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.ascii_histogram import ascii_histogram


class SkeletonsClustersConfig(RowLimitConfig):
    n_clusters: int = Field(
        default=20, description="The number of clusters to use for clustering"
    )


@asset(
    ins={
        "skeletons_embeddings": AssetIn(
            key=["skeletons_embeddings"],
        ),
    },
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
)
def skeletons_clusters(
    context: AssetExecutionContext,
    config: SkeletonsClustersConfig,
    skeletons_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    """
    Assigns clusters to skeletons using agglomerative clustering on their embeddings.

    Args:
        context: The asset execution context
        skeletons_embeddings: DataFrame containing the skeletons embeddings

    Returns:
        DataFrame containing skeletons with assigned clusters
    """
    conv_embeddings = np.stack(skeletons_embeddings["embedding"].to_list())

    # Perform agglomerative clustering
    clustering = AgglomerativeClustering(
        n_clusters=config.n_clusters, metric="euclidean", linkage="ward"
    )
    cluster_labels = clustering.fit_predict(conv_embeddings)

    # Split labels back into taxonomy and conversation parts
    conversation_clusters = cluster_labels

    # Create initial conversation result with clusters
    result = skeletons_embeddings.with_columns(
        [pl.Series(name="cluster_label", values=conversation_clusters)]
    )

    # Log cluster sizes
    cluster_sizes = (
        result.group_by("cluster_label")
        .agg([pl.count("cluster_label").alias("size")])
        .sort("cluster_label")
    )

    context.log.info(ascii_histogram(cluster_sizes.get_column("size").to_list()))

    return result
