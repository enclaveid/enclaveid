import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource


@asset(
    io_manager_key="parquet_io_manager",
    ins={"conversations_clusters": AssetIn(key=["conversations_clusters"])},
)
def conversation_clusters_summaries(
    context: AssetExecutionContext,
    conversations_clusters: pl.DataFrame,
    gemini_flash: BaseLlmResource,
) -> pl.DataFrame:
    llm = gemini_flash
    pass
