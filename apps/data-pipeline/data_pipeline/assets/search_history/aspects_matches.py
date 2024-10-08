import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.matching.aspects_bipartite_matching import (
    aspect_bipartite_matching,
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
def aspects_matches(
    context: AssetExecutionContext,
    aspects_embeddings: pl.DataFrame,
):
    matching_interest_ids, match_scores = aspect_bipartite_matching(
        aspects_embeddings.get_column("interest_id").to_list(),
        aspects_embeddings.get_column("aspects_embedding").to_list(),
        aspects_embeddings.get_column("category_label").to_list(),
    )

    return aspects_embeddings.with_columns(
        pl.Series("matching_interest_id", matching_interest_ids),
        pl.Series("match_score", match_scores),
    )
