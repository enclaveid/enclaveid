import time
from typing import List

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.local_llms.gemma27b import (
    Gemma27bResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.prompts.apsects_summarization import (
    get_aspects_summarization_prompt_sequence,
)


def parse_aspects_json(text: str) -> tuple[str | None, float | None, List[str] | None]:
    try:
        j = repair_json(text, return_objects=True)
        if isinstance(j, dict):
            res = (
                j.get("descriptive_category", None),
                j.get("sensitivity", None),
                j.get("all_aspects", None),
            )
        else:
            res = None, None, None
    except Exception:
        res = None, None, None

    return res


def parse_aspects_completions(summaries_completions: List[List[str]]):
    descriptive_categories, sensitivities, aspects = zip(
        *list(
            map(
                lambda x: parse_aspects_json(x[-1]) if x else (None, None, None),
                summaries_completions,
            )
        )
    )

    return {
        "cluster_title": descriptive_categories,
        "cluster_is_sensitive": sensitivities,
        "cluster_aspects": aspects,
    }


class ClusterSummariesConfig(RowLimitConfig):
    max_samples: int = Field(
        default=100,
        description="The maximum number of samples for each cluster to use for summarization.",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(),
)
async def cluster_summaries(
    context: AssetExecutionContext,
    config: ClusterSummariesConfig,
    gemma27b: Gemma27bResource,
    interests_clusters: pl.DataFrame,
):
    start_time = time.time()
    logger = get_logger(context)

    # Sample max_samples from each cluster
    sampled_df = (
        interests_clusters.drop("interest_id")
        .filter(pl.col("cluster_label") != -1)
        .filter(
            pl.int_range(pl.len()).shuffle().over("cluster_label") < config.max_samples
        )
    )

    # Sort by date and concat date and interests
    df = (
        sampled_df.sort(by=pl.col("date"))
        .with_columns(
            pl.concat_str(
                [
                    pl.col("date"),
                    pl.lit(":"),
                    pl.col("interests"),
                ],
            ).alias("date_interests")
        )
        .group_by("cluster_label")
        .agg(
            [
                pl.col("date_interests").str.concat("\n").alias("cluster_items"),
                pl.col("date").sort().alias("cluster_dates"),
                pl.col("merged_cluster_label")
                .unique()
                .map_elements(
                    lambda x: [i for i in x if i != -1], return_dtype=pl.List(pl.Int64)
                )
                .first(),
            ]
        )
    )

    prompt_sequences = [
        get_aspects_summarization_prompt_sequence(row["cluster_items"])
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} clusters...")

    (
        summaries_completions,
        conversations,
    ) = gemma27b.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    results = parse_aspects_completions(summaries_completions)
    results["conversations"] = conversations

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    invalid_results = result.filter(
        pl.col("cluster_title").is_null()
        | pl.col("cluster_is_sensitive").is_null()
        | pl.col("cluster_aspects").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="cluster_label", how="anti")

    return result
