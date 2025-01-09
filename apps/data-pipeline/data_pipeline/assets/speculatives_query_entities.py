from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
)


def get_seed_nodes_prompt(query_node: str) -> str:
    return dedent(
        f"""
            I want to substantiate this hypothetical claim about a user: "{query_node}"
            Specify a list of true claims that you would need to know about the user to be able to affirm the hypothetical above.
            Respond with an array of strings.
            """
    ).strip()


def parse_seed_nodes(completion: str) -> list[str] | None:
    try:
        result = repair_json(completion, return_objects=True)
        if result and isinstance(result, list):
            # Ensure list is flat and contains only strings
            if all(isinstance(item, str) for item in result):
                return result
            return None
        return None
    except Exception:
        return None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "recursive_causality": AssetIn(
            key=["recursive_causality"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def speculatives_query_entities(
    context: AssetExecutionContext,
    recursive_causality: pl.DataFrame,
    llama70b: BaseLlmResource,
    batch_embedder: BatchEmbedderResource,
) -> pl.DataFrame:
    query_nodes = (
        recursive_causality.filter(pl.col("node_type") == "speculative")
        .select(["label", "description"])
        .with_columns(
            pl.col("description")
            .map_elements(get_seed_nodes_prompt, return_dtype=pl.Utf8)
            .alias("prompt")
        )
    )

    context.log.info(f"Processing {len(query_nodes)} nodes...")

    prompt_sequences = [
        [prompt] for prompt in query_nodes.get_column("prompt").to_list()
    ]

    completions, cost = llama70b.get_prompt_sequences_completions_batch(
        prompt_sequences
    )

    context.log.info(f"Query nodes processing cost: {cost}")

    seed_nodes = [
        parse_seed_nodes(completion[-1]) if completion else None
        for completion in completions
    ]

    query_nodes = (
        query_nodes.drop("prompt")
        .with_columns(pl.Series(seed_nodes).alias("seed_nodes"))
        .explode("seed_nodes")
    )

    return query_nodes
