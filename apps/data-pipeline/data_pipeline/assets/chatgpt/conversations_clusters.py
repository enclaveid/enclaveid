from textwrap import dedent
from typing import Optional

import numpy as xp
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from hdbscan import HDBSCAN
from hdbscan.prediction import all_points_membership_vectors
from pydantic import Field
from sklearn.cluster import AgglomerativeClustering
from umap import UMAP

from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.clusters import (
    get_cluster_centroids,
    get_cluster_stats,
    get_soft_transitions,
)


class ConversationsClustersConfig(Config):
    fine_min_cluster_size: int = Field(
        default=2,
        description="Minimum number of samples in an activity cluster to be considered an interest.",
    )
    coarse_recluster_threshold: Optional[float] = Field(
        default=None,
        description=dedent(
            """
            Cosine distance threshold for merging similar activities into broader categories.
            If None, coarse_n_clusters must be provided.
            Takes priority over coarse_n_clusters.
            """
        ).strip(),
    )
    coarse_n_clusters: Optional[int] = Field(
        default=50,
        description=dedent(
            """
            Number of clusters to merge into. If None, coarse_recluster_threshold must be provided.
            """
        ).strip(),
    )


# TODO: We just do it on the CPU for now since it's fast enough for the amount of conversation data
@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "conversation_embeddings": AssetIn(
            key=["conversation_embeddings"],
        ),
    },
    # op_tags=get_k8s_rapids_config(),
)
def conversations_clusters(
    context: AssetExecutionContext,
    config: ConversationsClustersConfig,
    conversation_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    df = conversation_embeddings.filter(pl.col("analysis_embedding").is_not_null())

    # Convert the embeddings column to a 2D numpy array
    embeddings = xp.stack(df["analysis_embedding"].to_list())

    # Reduce the embeddings dimensions
    umap_model = UMAP(n_neighbors=15, n_components=100, min_dist=0.1, metric="cosine")
    reduced_data = umap_model.fit_transform(embeddings)

    # Move data to cpu if on gpu
    # if IS_RAPIDS:
    #     reduced_data = reduced_data.astype(xp.float64).get()
    # else:
    #     reduced_data = reduced_data.astype(xp.float64)

    reduced_data = reduced_data.astype(xp.float64)

    # Clustering for single interests
    clusterer = HDBSCAN(
        min_cluster_size=config.fine_min_cluster_size,
        # gen_min_span_tree=True,
        metric="euclidean",
        prediction_data=True,
    ).fit(reduced_data)

    membership_vectors = all_points_membership_vectors(clusterer)

    fine_cluster_labels_soft = membership_vectors.argmax(axis=1)

    # For each conversation, get the top 5 most probable clusters
    fine_cluster_labels_soft_transitions = get_soft_transitions(membership_vectors)

    # Set to True if any transition probability is 1.0 (core member)
    fine_cluster_labels_soft_is_core = xp.array(
        [
            max(transition["probability"] for transition in transitions) == 1.0
            for transitions in fine_cluster_labels_soft_transitions
        ],
        dtype=xp.bool_,
    ).flatten()

    context.log.info(f"Fine clusters: {len(fine_cluster_labels_soft)}")

    # Calculate centroids of fine clusters
    fine_cluster_centroids = get_cluster_centroids(
        reduced_data, fine_cluster_labels_soft
    )

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

    remapped_coarse_cluster_labels = xp.array(
        [
            coarse_cluster_labels[label] if label != -1 else label
            for label in fine_cluster_labels_soft
        ]
    ).flatten()

    context.log.info(get_cluster_stats(coarse_cluster_labels, prefix="coarse_"))

    result = df.with_columns(
        coarse_cluster_label=remapped_coarse_cluster_labels,  # type: ignore
        fine_cluster_label=fine_cluster_labels_soft,
        fine_cluster_is_core=fine_cluster_labels_soft_is_core,  # type: ignore
        fine_cluster_transitions=pl.Series(
            fine_cluster_labels_soft_transitions,
            dtype=pl.List(
                pl.Struct(
                    [
                        pl.Field("cluster_id", pl.Int64),
                        pl.Field("probability", pl.Float64),
                    ]
                )
            ),
        ),
    )

    # Reorder the columns for easier viewing in dtale
    reordered_columns = [
        "start_date",
        "start_time",
        "title",
        "is_emotional",
        "coarse_cluster_label",
        "fine_cluster_label",
        "fine_cluster_is_core",
        "fine_cluster_transitions",
    ]

    sorted_result = result.select(
        *[pl.col(col) for col in reordered_columns],
        pl.all().exclude(reordered_columns),
    ).sort(
        "coarse_cluster_label",
        "fine_cluster_label",
        "start_date",
        "start_time",
        descending=[True, True, False, False],
    )

    return sorted_result
