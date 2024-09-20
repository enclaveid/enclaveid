import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_maximally_dissimilar_embeddings import (
    get_maximally_dissimilar_embeddings,
)


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_embeddings": AssetIn(key=["interests_embeddings"])},
    op_tags=get_k8s_rapids_config(),
)
def dissimilar_funny_interests(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    interests_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    """
    Given a list of search history chunks, return a list of the most dissimilar funny interests.
    """

    df = interests_embeddings.slice(0, config.row_limit).filter(
        pl.col("interests_quirkiness").eq(True)
    )

    if df.is_empty():
        return pl.DataFrame()

    ranking = get_maximally_dissimilar_embeddings(df.select("embeddings").to_numpy())

    result = df.with_columns(dissimilarity_rank=pl.Series(ranking))

    # Columns: interest_id, date, interests, interests_quirkiness, embeddings, dissimilarity_rank
    return result
