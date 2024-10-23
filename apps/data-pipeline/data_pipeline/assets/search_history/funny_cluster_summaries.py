import time

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.local_llms.gemma27b import (
    Gemma27bResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import (
    parse_funny_summaries,
)
from data_pipeline.utils.prompts.funny_summarization import (
    get_funny_summarization_prompt_sequence,
)


class ClusterSummariesConfig(RowLimitConfig):
    debug: bool = Field(
        default=True,
        description="Set to True to materialize the cluster_summaries_debug asset, which includes the full assistant replies.",
    )
    max_samples: int = Field(
        default=100,
        description="The maximum number of samples for each cluster to use for summarization.",
    )


# TODO: break this asset down into one asset per llm invocation
# otherwise when the vm gets evicted we have to redo everything
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
async def funny_cluster_summaries(
    context: AssetExecutionContext,
    config: ClusterSummariesConfig,
    gemma27b: Gemma27bResource,
    interests_clusters: pl.DataFrame,
):
    start_time = time.time()
    logger = get_logger(context)

    # Sample max_samples from each cluster
    sampled_df = (
        interests_clusters.slice(0, config.row_limit)
        .drop("interest_id")
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
                    pl.lit("-"),
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
                ),
            ]
        )
    )

    prompt_sequences = [
        get_funny_summarization_prompt_sequence(row["cluster_items"])
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

    results = []
    for completions, conversation in zip(summaries_completions, conversations):
        title, summary, image_description = parse_funny_summaries(completions[-1])
        results.append(
            {
                "cluster_title": title,
                "cluster_summary": summary,
                "image_description": image_description,
                "conversation": conversation,
            }
        )

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    invalid_results = result.filter(
        pl.col("cluster_title").is_null()
        | pl.col("cluster_summary").is_null()
        | pl.col("image_description").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="cluster_label", how="anti")

    # Columns: date, interests, cluster_label, cluster_title, cluster_summary, is_sensitive, social_likelihood
    return result
