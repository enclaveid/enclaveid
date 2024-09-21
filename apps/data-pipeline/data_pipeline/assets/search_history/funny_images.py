import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.assets.search_history.funny_cluster_summaries import (
    user_partitions_def,
)
from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.resources.inference.image_generator_resource import (
    ImageGeneratorResource,
)
from data_pipeline.utils.batch_save_images import (
    batch_save_images,
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
) -> None:
    df = funny_cluster_summaries.slice(0, config.row_limit)

    prompts = df.get_column("image_description").to_list()
    cluster_labels = df.get_column("cluster_label").to_list()
    image_dict = image_generator.generate_images(prompts, cluster_labels)
    batch_save_images(image_dict, context.partition_key)
