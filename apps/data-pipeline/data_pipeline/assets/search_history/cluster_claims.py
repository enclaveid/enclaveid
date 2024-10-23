import time
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
from data_pipeline.resources.inference.local_llms.llama70b_nemotron import (
    Llama70bNemotronResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.prompts.claim_generation import (  # You'll need to create this
    get_claim_generation_prompt_sequence,
)


def parse_claims_json(text: str) -> List[Dict[str, Any]] | None:
    try:
        j = repair_json(text, return_objects=True)
        if isinstance(j, dict) and "strong" in j and "weak" in j:
            claims = []
            # Process strong claims
            for claim in j["strong"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": 1.0,
                        "claim_type": "strong",
                    }
                )
            # Process weak claims
            for claim in j["weak"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": claim.get("confidence", 0.0),
                        "claim_type": "weak",
                    }
                )
            return claims
    except Exception:
        return None


def parse_claims_completions(claims_completions: List[List[str]]):
    all_claims = []
    for completion in claims_completions:
        if completion:
            claims = parse_claims_json(completion[-1])
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
    llama70b_nemotron: Llama70bNemotronResource,
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

    # Sample config.row_limit clusters for testing if any
    df = df.slice(0, config.row_limit)

    year_start = interests_clusters.select(pl.min("date").dt.year()).item()
    year_end = interests_clusters.select(pl.max("date").dt.year()).item()
    records_count = interests_clusters.shape[0]

    prompt_sequences = [
        get_claim_generation_prompt_sequence(
            row["cluster_items"], year_start, year_end, records_count
        )
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} clusters...")

    (
        claims_completions,
        conversations,
    ) = llama70b_nemotron.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    results = parse_claims_completions(claims_completions)
    # results["conversations"] = conversations

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    invalid_results = result.filter(pl.col("claims").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} claims.")

    result = result.join(invalid_results, on="cluster_label", how="anti")

    return result
