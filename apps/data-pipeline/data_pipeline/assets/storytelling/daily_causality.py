import json
from typing import List

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    asset,
)

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.consts import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.prompts.causal_inference import (
    get_causal_inference_prompt_sequence,
    parse_causal_inference_json,
)
from data_pipeline.utils.prompts.causal_inference_v2 import (
    get_cross_chunk_causal_inference_prompt_sequence,
)


def parse_causal_inference_completions(
    completions: List[List[str]], dates: List[int]
) -> pl.DataFrame:
    rows = []
    for completion, date, chunk_id in zip(completions, dates, range(len(completions))):
        if completion:
            result = parse_causal_inference_json(completion[-1])

            if result:
                for cluster_id, subcluster in enumerate(result["subclusters"]):
                    rows.append(
                        {
                            "id": chunk_id * len(result["subclusters"]) + cluster_id,
                            "date": date,
                            "start_time": subcluster["start_time"],
                            "end_time": subcluster["end_time"],
                            "description": subcluster["description"],
                        }
                    )

    return pl.DataFrame(
        rows,
        schema={
            "id": pl.UInt32,
            "date": pl.Date,
            "start_time": pl.String,
            "end_time": pl.String,
            "description": pl.String,
        },
    )


TEST_ROW_LIMIT = 10 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "interests": AssetIn(
            key=["interests"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(),
)
async def daily_causality(
    context: AssetExecutionContext,
    config: Config,
    llama70b_nemotron: BaseLlmResource,
    interests: pl.DataFrame,
):
    llm_resource = llama70b_nemotron
    logger = get_logger(context)

    df = (
        interests.sort(pl.col("date"))
    )

    # Sample TEST_ROW_LIMIT days for testing if any
    df = df.slice(0, TEST_ROW_LIMIT)

    prompt_sequences = []
    dates = []
    for row in df.to_dicts():
        for chunk in row["interests"]:
            prompt_sequences.append(get_causal_inference_prompt_sequence(chunk))
            dates.append(row["date"])

    logger.info(f"Processing {len(prompt_sequences)} days...")

    (
        completions,
        cost,
    ) = llm_resource.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} days.")
    logger.info(f"Execution cost: ${cost:.2f}")

    subclusters = parse_causal_inference_completions(completions, dates)

    prompt_sequences = (
        subclusters.group_by("date")
        .agg(
            pl.struct(subclusters.columns)
            .map_batches(
                lambda rows: get_cross_chunk_causal_inference_prompt_sequence(
                    [
                        json.dumps(
                            {k: v for k, v in row.items() if k != "date"},
                            indent=2,
                        )
                        for row in rows.to_list()
                    ]
                )
            )
            .alias("prompt_sequences"),
        )
        .get_column("prompt_sequences")
        .to_list()
    )

    logger.info(prompt_sequences[0])

    (
        completions,
        cost,
    ) = llm_resource.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    result = result.join(df, on="date", how="left")

    invalid_results = result.filter(pl.col("narrative").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} results.")

    result = result.join(invalid_results, on="date", how="anti")

    return result
