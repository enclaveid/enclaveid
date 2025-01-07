from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource


def get_causality_prompt_sequence(node: dict) -> list[str]:
    similar_nodes_text = "\n".join(
        f"{similar['label']}: {similar['description']}"
        for similar in node["similar_nodes"]
    )

    return [
        dedent(
            f"""
            You are a careful analyst determining potential causal relationships between events or concepts.

            MAIN EVENT:
            {node['description']}

            POTENTIALLY RELATED EVENTS:
            {similar_nodes_text}

            Question: Which of the labeled events, if any, could have been CAUSED BY the main event?
            Consider only direct causal relationships where the main event could be a clear contributing factor to the other event.

            Please respond with a JSON array of objects, where each object represents a causal relationship and contains:
            - "label": the label of the caused event
            - "explanation": brief explanation of the causal relationship

            If no causal relationships exist, respond with an empty array: []

            Example response:
            [
                {
                    "label": "EVT_123",
                    "explanation": "The main event's market disruption directly led to this supply chain issue"
                },
                {
                    "label": "EVT_456",
                    "explanation": "The technology introduced in the main event enabled this development"
                }
            ]

            Remember:
            - Only include strong, direct causal relationships
            - The cause must precede the effect
            - Correlation alone is not causation
            - If uncertain, err on the side of caution
            """
        ).strip()
    ]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "speculatives_substantiation": AssetIn(
            key=["speculatives_substantiation"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def speculatives_causality(
    context: AssetExecutionContext,
    llama70b: BaseLlmResource,
    speculatives_substantiation: pl.DataFrame,
) -> pl.DataFrame:
    llm = llama70b
    logger = context.log

    nodes = speculatives_substantiation.to_dicts()
    prompt_sequences = [get_causality_prompt_sequence(node) for node in nodes]

    logger.info(f"Processing causality analysis for {len(prompt_sequences)} nodes...")

    completions, cost = llm.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} nodes.")
    logger.info(f"Execution cost: ${cost:.2f}")

    # Process completions into results
    results = [
        {
            "label": node["label"],
            "causality_raw": completion[-1] if completion else None,
            "causality": repair_json(completion[-1], return_objects=True)
            if completion
            else None,
        }
        for node, completion in zip(nodes, completions)
    ]

    result_df = pl.DataFrame(results)

    # Join with original DataFrame
    final_df = speculatives_substantiation.join(result_df, on="label", how="left")

    # Filter out null results
    invalid_results = final_df.filter(pl.col("causality_analysis").is_null())
    if invalid_results.height > 0:
        logger.warning(f"Found {invalid_results.height} invalid causality analyses.")

    return final_df.filter(pl.col("causality_analysis").is_not_null())
