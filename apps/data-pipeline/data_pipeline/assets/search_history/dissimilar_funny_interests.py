import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_rapids_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_maximally_dissimilar_embeddings import (
    get_maximally_dissimilar_embeddings,
)


class DissimilarFunnyInterestsConfig(RowLimitConfig):
    max_count: int = Field(
        default=1000,
        description="The number of maximally dissimilar funny interests to return.",
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_embeddings": AssetIn(key=["interests_embeddings"])},
    op_tags=get_k8s_rapids_config(1),
)
def dissimilar_funny_interests(
    context: AssetExecutionContext,
    config: DissimilarFunnyInterestsConfig,
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

    indices = get_maximally_dissimilar_embeddings(
        df.select("embeddings").to_numpy(), config.max_count
    )

    result = df.with_columns(maximally_dissimilar=pl.arange(0, len(df)).is_in(indices))

    # Columns: interest_id, date, interests, interests_quirkiness, embeddings, maximally_dissimilar
    return result
