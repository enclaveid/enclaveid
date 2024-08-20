import time
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetOut,
    multi_asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.llm_inference.llama70b_quantized_resource import (
    Llama70bQuantizedResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import parse_cluster_categories_json


def get_categorization_prompt(cluster_items: str):
    return dedent(
        f"""
        Analyze the given cluster of search activity.
        When analyzing the cluster, consider the following:
        - Look for recurring themes or subjects in the search queries
        - Identify the broadest categories that still maintain specificity
        - Ensure that the chosen tags collectively cover the majority of the search activity
        - Be prepared to use fewer than 3 tags if they adequately describe the cluster
        - Provide a clear rationale for why the chosen tags best represent the search activity

        Examples:

        A. Computer Hardware Research Cluster:
        Raw Data:
        2023-06-28: Researching laptops for potential purchase
        2023-06-28: considering purchasing MacBook Air M2
        2023-06-30: evaluating Apple M2 chip performance vs AMD Ryzen 5 5600X for desktop/laptop applications
        2023-06-30: Comparing AMD Ryzen 5 5600X performance with other CPUs for gaming/general computing
        2023-07-26: comparing MacBook Pro and ThinkPad X1 Carbon features
        2023-07-26: Assessing the Intel Core i7-9750H's performance relative to the i5-8365U
        2023-08-07: researching T4 GPU capabilities and memory
        2023-08-08: exploring general information on A100 GPU

        Tags:
        1. Computer Hardware Research
        2. Laptop Comparison and Troubleshooting
        3. GPU/CPU Performance Evaluation

        Explanation: These tags cover the main themes of researching various computer components, comparing laptop models, and evaluating GPU/CPU performance for different applications.

        B. Travel Planning Cluster:
        Raw Data:
        2023-08-01: best beaches in Thailand
        2023-08-02: budget hostels in Barcelona
        2023-08-03: top tourist attractions in New York City
        2023-08-04: how to find cheap flights to Europe
        2023-08-05: best time to visit Japan for cherry blossoms
        2023-08-06: affordable Airbnb options in Paris
        2023-08-07: must-try street food in Mexico City
        2023-08-08: backpacking essentials for Southeast Asia trip

        Tags:
        1. Destination Research
        2. Budget Accommodation Options

        Explanation: These two tags sufficiently cover the cluster, focusing on exploring potential travel locations and finding affordable places to stay.
        A third tag wasn't necessary to encompass the search activity.

        Comclude your analysis with a JSON as follows:
        {{
          "cluster_categories": [a list with the chosen tags]
        }}

        Here is the cluster of search activity:
        {cluster_items}
        """
    ).strip()


class ClusterSummariesConfig(RowLimitConfig):
    debug: bool = Field(
        default=True,
        description="Set to True to materialize the cluster_categories_debug asset, which includes the full assistant replies.",
    )


@multi_asset(
    partitions_def=user_partitions_def,
    outs={
        "cluster_categories": AssetOut(
            key=["cluster_categories"],
            io_manager_key="parquet_io_manager",
            is_required=True,
        ),
        "cluster_categories_debug": AssetOut(
            key=["cluster_categories_debug"],
            io_manager_key="parquet_io_manager",
            is_required=False,
        ),
    },
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    op_tags=get_k8s_vllm_config(2),
)
async def cluster_categories(
    context: AssetExecutionContext,
    config: ClusterSummariesConfig,
    llama70b_quantized: Llama70bQuantizedResource,
    interests_clusters: pl.DataFrame,
):
    start_time = time.time()
    logger = get_logger(context)

    df = (
        interests_clusters.sort(by=pl.col("date"))
        .with_columns(
            pl.concat_str([pl.col("date"), pl.col("interests")], separator=":").alias(
                "date_interests"
            )
        )
        .group_by("category_cluster_label")
        .agg(
            [
                pl.col("date_interests").str.concat("\n").alias("cluster_items"),
                pl.col("date").sort().alias("cluster_dates"),
            ]
        )
        .filter(pl.col("category_cluster_label") != -1)
        .slice(0, config.row_limit)
    )

    prompt_sequences = [
        [
            get_categorization_prompt(row["cluster_items"]),
        ]
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} clusters...")

    (
        completions,
        conversations,
    ) = llama70b_quantized.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    results = {
        "cluster_categories": list(
            map(lambda x: parse_cluster_categories_json(x[0]) if len(x) > 0 else [], completions)
        ),
        "conversations": conversations,
    }

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    debug_dataframe = result.clone()

    invalid_results = result.filter(pl.col("cluster_categories").list.len() == 0)

    if invalid_results.height > 0:
        logger.warning(f"Found {invalid_results.height} invalid categories.")

    result = result.join(invalid_results, on="category_cluster_label", how="anti").drop(
        ["conversations"]
    )

    if config.debug:
        return result, debug_dataframe
    else:
        return result
