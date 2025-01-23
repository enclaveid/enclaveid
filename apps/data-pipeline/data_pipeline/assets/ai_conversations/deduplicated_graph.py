from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource


def get_description_consolidation_prompt_sequence(descriptions: list[str]) -> list[str]:
    descriptions_text = "\n".join(f"- {desc}" for desc in descriptions)
    return [
        dedent(
            f"""
            Given multiple descriptions of the same concept, create a single comprehensive description that:
            - Captures all unique information from the input descriptions
            - Eliminates redundancy
            - Maintains the same writing style as the input descriptions
            - Preserves specific details and examples when present

            Here are the descriptions to consolidate:
            {descriptions_text}

            Provide only the consolidated description without any additional commentary.
            """
        ).strip()
    ]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph_raw": AssetIn(
            key=["deduplicated_graph_raw"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def deduplicated_graph(
    context: AssetExecutionContext,
    gpt4o: BaseLlmResource,
    deduplicated_graph_raw: pl.DataFrame,
) -> pl.DataFrame:
    logger = context.log

    # Filter for nodes that have multiple descriptions
    nodes_to_process = deduplicated_graph_raw.filter(pl.col("frequency") > 1)
    logger.info(
        f"Processing {len(nodes_to_process)} nodes with multiple descriptions..."
    )

    prompt_sequences = [
        get_description_consolidation_prompt_sequence(row["merged_descriptions"])
        for row in nodes_to_process.to_dicts()
    ]

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(prompt_sequences)

    logger.info(f"Done processing. Execution cost: ${cost:.2f}")

    # Create a new DataFrame with just labels and consolidated descriptions
    consolidated_df = pl.DataFrame(
        {
            "label": nodes_to_process.get_column("label"),
            "new_description": [
                completion[-1] if completion else row["description"]
                for row, completion in zip(nodes_to_process.to_dicts(), completions)
            ],
        }
    )

    # Join the consolidated descriptions back to the original DataFrame
    result = (
        deduplicated_graph_raw.join(consolidated_df, on="label", how="left")
        .with_columns(
            [
                pl.col("new_description")
                .fill_null(pl.col("description"))
                .alias("description")
            ]
        )
        .drop("new_description")
    )

    return result
