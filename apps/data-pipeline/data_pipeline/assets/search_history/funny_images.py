import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from upath import UPath

from data_pipeline.assets.search_history.funny_cluster_summaries import (
    user_partitions_def,
)
from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.inference.image_generator_resource import (
    ImageGeneratorResource,
)


@asset(
    partitions_def=user_partitions_def,
    ins={
        "funny_cluster_summaries": AssetIn(
            key=["funny_cluster_summaries"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(4),
)
async def funny_images(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    image_generator: ImageGeneratorResource,
    funny_cluster_summaries: pl.DataFrame,
) -> pl.DataFrame:
    df = funny_cluster_summaries.slice(0, config.row_limit)

    prompts = df.get_column("image_description").to_list()
    cluster_labels = df.get_column("cluster_label").to_list()
    images = image_generator.generate_images(prompts)

    images_folder: UPath = (
        DAGSTER_STORAGE_BUCKET / "funny_images" / context.partition_key
    )
    images_folder.mkdir(parents=True, exist_ok=True)
    image_paths = []

    for cluster_label, image in zip(cluster_labels, images):
        image_path = images_folder / f"{cluster_label}.png"
        image.save(image_path)
        image_paths.append(image_path)

    return df.with_columns(image_path=pl.Series(image_paths))
