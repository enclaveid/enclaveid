import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
import faiss


@asset(
    partitions_def=user_partitions_def,
    ins={
        "stories_outlines": AssetIn(
            key=["stories_outlines"],
        ),
        "conversation_embeddings": AssetIn(
            key=["conversation_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def stories_grounding(
    context: AssetExecutionContext,
    stories_outlines: pl.DataFrame,
    conversation_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    # Your implementation here
    pass
