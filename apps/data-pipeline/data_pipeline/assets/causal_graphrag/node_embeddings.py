import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.consts import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.embeddings.base_embedder_resource import (
    BaseEmbedderResource,
)
from data_pipeline.utils.get_logger import get_logger

TEST_LIMIT = 100 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversation_claims": AssetIn(
            key=["conversation_claims"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config() if get_environment() != "LOCAL" else {},
)
async def node_embeddings(
    context: AssetExecutionContext,
    nvembed: BaseEmbedderResource,
    conversation_claims: pl.DataFrame,
) -> pl.DataFrame:
    logger = get_logger(context)
    result = conversation_claims.slice(0, TEST_LIMIT).clone()
    categories = ["speculatives", "inferrables", "observables"]

    # Convert to Python dictionaries for easier processing
    rows = result.to_dicts()

    # We'll keep track of which embedding belongs to which row and category
    all_descriptions = []
    # Store metadata about where each description came from
    description_mapping = []  # List of (row_idx, category, position_in_category)

    # First pass: collect all descriptions and their metadata
    for row_idx, row in enumerate(rows):
        for category in categories:
            claims = row[category]
            if claims:  # If we have claims in this category
                for position, claim in enumerate(claims):
                    all_descriptions.append(claim["description"])
                    description_mapping.append((row_idx, category, position))

    # Initialize our result structure
    row_embeddings = {
        category: [[] for _ in range(len(rows))] for category in categories
    }

    # Get all embeddings in one batch if we have any descriptions
    if all_descriptions:
        all_embeddings, total_cost = nvembed.get_embeddings(
            pl.Series(name="descriptions", values=all_descriptions)
        )
        logger.info(f"Total embedding cost: ${total_cost:.2f}")

        # Now distribute embeddings back to their original positions
        for embedding_idx, (row_idx, category, position) in enumerate(
            description_mapping
        ):
            # Get the embedding for this description
            embedding = all_embeddings[embedding_idx]

            # Some categories might not have had all positions filled consecutively
            # Ensure we have a list that can accommodate the position
            while len(row_embeddings[category][row_idx]) <= position:
                row_embeddings[category][row_idx].append(None)

            # Place the embedding in its correct position
            row_embeddings[category][row_idx][position] = embedding

    # Add embedding columns to the result DataFrame
    for category in categories:
        result = result.with_columns(
            pl.Series(name=f"{category}_embeddings", values=row_embeddings[category])
        )
        logger.info(f"Mapped embeddings for {category}")

    # Output:
    # ... | speculatives_embeddings | inferrables_embeddings  | observables_embeddings
    # ----|-------------------------|-------------------------|------------------------
    # ... | List[List[float]]       | List[List[float]]       | List[List[float]]
    return result
