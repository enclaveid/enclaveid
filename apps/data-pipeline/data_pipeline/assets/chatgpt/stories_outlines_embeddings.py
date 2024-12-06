import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.embeddings.nvembed_resource import NVEmbedResource


@asset(
    io_manager_key="parquet_io_manager",
    partitions_def=user_partitions_def,
    ins={
        "stories_outlines": AssetIn(key=["stories_outlines"]),
    },
    op_tags=get_k8s_vllm_config(),
)
def stories_outlines_embeddings(
    context: AssetExecutionContext,
    stories_outlines: pl.DataFrame,
    nvembed: NVEmbedResource,
) -> pl.DataFrame:
    # Extract descriptions separately
    emotional_descriptions = stories_outlines["emotional_anchors"].map_elements(
        lambda x: " ".join(anchor["description"] for anchor in x) if x else ""
    )
    transition_descriptions = stories_outlines["transitions"].map_elements(
        lambda x: " ".join(transition["description"] for transition in x) if x else ""
    )

    # Get separate embeddings for each
    emotional_embeddings, emotional_cost = nvembed.get_embeddings(
        emotional_descriptions
    )
    transition_embeddings, transition_cost = nvembed.get_embeddings(
        transition_descriptions
    )

    total_cost = emotional_cost + transition_cost
    context.log.info(f"Estimated cost: ${total_cost:.2f}")

    return stories_outlines.with_columns(
        emotional_anchors_embedding=emotional_embeddings,
        transitions_embedding=transition_embeddings,
    )
