from typing import Any, Dict, List

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
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.prompts.claim_generation_v2 import (
    get_claim_generation_prompt_sequence,
)


def parse_claims_json(text: str, cluster_label: int) -> List[Dict[str, Any]] | None:
    try:
        j = repair_json(text, return_objects=True)
        if isinstance(j, dict) and "inferrables" in j and "speculatives" in j:
            claims = []
            for claim in j["inferrables"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": claim.get("confidence", 0.0),
                        "claim_type": "inferrable",
                        "cluster_label": cluster_label,
                    }
                )
            for claim in j["speculatives"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": claim.get("confidence", 0.0),
                        "claim_type": "speculative",
                        "cluster_label": cluster_label,
                    }
                )
            return claims
    except Exception:
        return None


def parse_claims_completions(
    claims_completions: List[List[str]], cluster_labels: List[int]
):
    all_claims = []
    for completion, cluster_label in zip(claims_completions, cluster_labels):
        if completion:
            claims = parse_claims_json(completion[-1], cluster_label)

            if claims:
                all_claims.extend(claims)
            else:
                all_claims.append(
                    {
                        "from_date": None,
                        "to_date": None,
                        "claim": None,
                        "confidence": None,
                        "claim_type": None,
                        "cluster_label": cluster_label,
                    }
                )
        else:
            all_claims.append(
                {
                    "from_date": None,
                    "to_date": None,
                    "claim": None,
                    "confidence": None,
                    "claim_type": None,
                    "cluster_label": cluster_label,
                }
            )

    return all_claims


class ClaimGenerationConfig(RowLimitConfig):
    max_samples: int = Field(
        default=100,
        description="The maximum number of samples for each cluster to use for claim generation.",
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
async def cluster_claims(
    context: AssetExecutionContext,
    config: ClaimGenerationConfig,
    gemini_flash: BaseLlmResource,
    interests_clusters: pl.DataFrame,
):
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

    # Sample config.row_limit clusters for testing if any
    df = df.slice(0, config.row_limit)

    # year_start = interests_clusters.select(pl.min("date").dt.year()).item()
    # year_end = interests_clusters.select(pl.max("date").dt.year()).item()
    # records_count = interests_clusters.shape[0]

    prompt_sequences = []
    cluster_labels = []
    for row in df.to_dicts():
        prompt_sequences.append(
            get_claim_generation_prompt_sequence(row["cluster_items"])
        )
        cluster_labels.append(row["cluster_label"])

    logger.info(f"Processing {len(prompt_sequences)} clusters...")

    (
        claims_completions,
        cost,
    ) = gemini_flash.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} clusters.")
    logger.info(f"Execution cost: ${cost:.2f}")

    results = parse_claims_completions(claims_completions, cluster_labels)

    result = pl.DataFrame(results)

    invalid_results = result.filter(pl.col("claim").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} claims.")

    result = result.join(invalid_results, on="cluster_label", how="anti")

    return result
