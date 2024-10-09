import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.matching.aspects_bipartite_matching import (
    aspects_bipartite_matching,
)


class AspectsMatchesConfig(RowLimitConfig):
    aspect_similarity_threshold: float = Field(
        default=0.7,
        description="The threshold for the cosine similarity between aspects to consider a match.",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "aspects_embeddings": AssetIn(
            key=["aspects_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_rapids_config(),
)
async def aspects_matches(
    context: AssetExecutionContext,
    config: AspectsMatchesConfig,
    aspects_embeddings: pl.DataFrame,
):
    matching_cluster_labels, match_scores = await aspects_bipartite_matching(
        aspects_embeddings.get_column("cluster_label").to_list(),
        aspects_embeddings.get_column("aspects_embeddings").to_list(),
        aspects_embeddings.get_column("merged_cluster_label")
        .to_numpy()
        .flatten()
        .tolist(),
        aspect_similarity_threshold=config.aspect_similarity_threshold,
    )

    return aspects_embeddings.with_columns(
        pl.Series("matching_cluster_label", matching_cluster_labels),
        pl.Series("match_score", match_scores),
    )
