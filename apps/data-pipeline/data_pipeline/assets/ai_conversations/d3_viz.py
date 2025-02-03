import polars as pl
import umap.umap_ as umap
from dagster import AssetExecutionContext, AssetIn, asset
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.partitions import user_partitions_def


class D3VizConfig(RowLimitConfig):
    n_neighbors: int = Field(default=15, description="UMAP n_neighbors parameter")
    min_dist: float = Field(default=0.1, description="UMAP min_dist parameter")
    random_state: int = Field(default=42, description="Random seed for reproducibility")
    n_umap_components: int = Field(default=2, description="Number of UMAP components")


@asset(
    io_manager_key="parquet_io_manager",
    partitions_def=user_partitions_def,
    ins={
        "recursive_causality": AssetIn(key=["recursive_causality"]),
    },
)
def d3_viz(
    context: AssetExecutionContext,
    recursive_causality: pl.DataFrame,
    config: D3VizConfig,
) -> pl.DataFrame:
    logger = context.log

    df = recursive_causality.filter(
        pl.col("node_type").is_in(["inferrable", "observable"])
    ).select(
        [
            "label",
            "category",
            "node_type",
            "description",
            "embedding",
            "start_date",
            "end_date",
            "edges",
        ]
    )

    # Run UMAP
    logger.info("Running UMAP dimensionality reduction")
    reducer = umap.UMAP(
        n_neighbors=config.n_neighbors,
        min_dist=config.min_dist,
        n_components=config.n_umap_components,
        random_state=config.random_state,
        verbose=True,
    )
    umap_coords = reducer.fit_transform(df["embedding"].to_list())

    node_coords = []
    for coord in umap_coords:
        coords_dict = {f"umap_{i}": coord for i, coord in enumerate(coord)}
        node_coords.append(coords_dict)

    return df.with_columns(
        umap_coords=pl.Series(name="umap_coords", values=node_coords)
    ).drop(["embedding"])
