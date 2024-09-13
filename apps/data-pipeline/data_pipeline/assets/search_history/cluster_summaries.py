import time
from datetime import datetime
from enum import Enum
from textwrap import dedent
from typing import Tuple

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetOut,
    multi_asset,
)
from pydantic import BaseModel, Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.llm_inference.gemma27b_resource import (
    Gemma27bResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import (
    parse_cluster_classification_json,
    parse_summaries_completions,
)


class ActivityType(str, Enum):
    knowledge_progression = "knowledge_progression"
    reactive_needs = "reactive_needs"
    unknown = "unknown"


class InitialClassificationResult(BaseModel):
    activity_type: ActivityType
    sensitive: bool
    explanation: str
    confidence: float


def get_initial_classification_prompt(search_activity: str):
    return dedent(
        f"""
        Analyze the provided cluster of search activity data for a single topic. Determine whether this cluster primarily represents:
        1. A progression in knowledge acquisition and long-term interest, or
        2. Reactive searches driven by occasional or recurring needs.

        Consider the following factors in your analysis:
        - Frequency and regularity of searches
        - Diversity of subtopics within the main theme
        - Presence of time-bound or event-specific queries
        - Indications of recurring but intermittent activities
        - Signs of problem-solving for specific occasions rather than general learning

        Provide a classification as either 'knowledge_progression' or 'reactive_needs', along with a confidence score (0-100%).
        Offer a an explaination supporting your classification, highlighting the key factors that influenced your decision.
        Additionally, assess whether the topic is sensitive in nature, particularly regarding psychosocial aspects.

        Conclude your analysis with a JSON as follows:
        {{
          "activity_type": "knowledge_progression" or "reactive_needs" or "unknown",
          "sensitive": true or false,
          "confidence": 0.0-1.0
        }}

        {search_activity}
        """
    )


class SummarizationResult(BaseModel):
    title: str
    summary: str


def get_summarization_prompt(initial_classification_result: str) -> str:
    CLUSTER_SUMMARIZATION_FORMAT = dedent(
        """
        Pay particular attention to the elements tagged as "UNIQUE" in the cluster, and make sure to mention them in the summary.

        Finally, provide the most detailed possible category that captures all the topics of the activity.

        Conclude your analysis with a JSON as follows:
        {
          "title": "The category you found",
          "summary": "Your summary"
        }
        """
    )

    UNKNOWN_SUMMARY = dedent(
        """
        The search activity does not fit the criteria for either knowledge progression or reactive needs.
        Explain why the activity is ambiguous and provide a brief summary of the main topics covered.

        {CLUSTER_SUMMARIZATION_FORMAT}
        """
    )

    key = parse_cluster_classification_json(initial_classification_result)[0]

    if key is None:
        return UNKNOWN_SUMMARY
    else:
        return {
            "unknown": UNKNOWN_SUMMARY,
            "reactive_needs": dedent(
                f"""
              Summarize the reactive search activity by taking into account the time periods
              and what the user will have obtained at the end of their search. Describe:

              - The main category of reactive needs
              - The specific types of occasions or needs
              - Frequency pattern of these needs
              - User's apparent level of experience in addressing these needs

              {CLUSTER_SUMMARIZATION_FORMAT}
              """
            ),
            "knowledge_progression": dedent(
                f"""
              Summarize the knowledge progression by taking into account the time periods and how each
              incremental chunk expands the user's knowledge horizontally or vertically. Describe:

              - The main topic or starting point of interest
              - Key areas or subtopics the user explored from this starting point
              - How the user's understanding seemed to deepen or branch out in each area
              - Any connections or jumps between different areas of exploration
              - The most advanced or recent concepts the user has searched for

              Conclude with the overall trajectory and breadth of the user's learning path.

              {CLUSTER_SUMMARIZATION_FORMAT}
              """
            ),
        }[key]


class SocialLikelihoodResult(BaseModel):
    likelihood: float
    explanation: str


SOCIAL_LIKELIHOOD_PROMPT = dedent(
    f"""
        Would this type of activity be interesting to connect over with other similar users?
        In your analysis, take into account:
        - [IMPORTANT] Whether the topic itself is generally boring (e.g., main job, taxation, laundry) or engaging (e.g., arts, games, hobbies)
        - How deeply engaged the user seems to be with the topic
        - Whether the user engaged in very niche areas of the topic
        - If the activity is sensitive, assume the user is willing to share it with others
        - The current date is {datetime.today().strftime('%Y-%m-%d')}, if the activity is reactive, consider that it might not be relevant for the user if they did it long ago

        Provide a social likelihood score from 0 to 100% in JSON as follows:
        {{
          "likelihood": 0.0 - 1.0,
        }}
        """
)

SummariesCompletions = Tuple[
    InitialClassificationResult, SummarizationResult, SocialLikelihoodResult
]


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
@multi_asset(
    partitions_def=user_partitions_def,
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    outs={
        "cluster_summaries": AssetOut(
            key=["cluster_summaries"],
            io_manager_key="parquet_io_manager",
            is_required=True,
        ),
        # "cluster_summaries_debug": AssetOut(
        #     key=["cluster_summaries_debug"],
        #     io_manager_key="parquet_io_manager",
        #     is_required=False,
        # ),
    },
    op_tags=get_k8s_vllm_config(2),
    # retry_policy=spot_instance_retry_policy,
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
                    pl.when(pl.col("interests_uniqueness").eq(True))
                    .then(pl.lit("UNIQUE:"))
                    .otherwise(pl.lit("")),
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
                pl.col("category_cluster_label")
                .unique()
                .map_elements(
                    lambda x: [i for i in x if i != -1], return_dtype=pl.List(pl.Int64)
                )
                .alias("category_cluster_labels"),
            ]
        )
    )

    prompt_sequences = [
        [
            get_initial_classification_prompt(row["cluster_items"]),
            get_summarization_prompt,
            SOCIAL_LIKELIHOOD_PROMPT,
        ]
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} clusters...")

    (
        summaries_completions,
        conversations,
    ) = gemma27b.get_prompt_sequences_completions_batch(
        prompt_sequences,
        # [
        #     InitialClassificationResult,
        #     SummarizationResult,
        #     SocialLikelihoodResult,
        # ],
    )
    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    results = parse_summaries_completions(summaries_completions)
    results["conversations"] = conversations

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    # debug_dataframe = result.clone()

    invalid_results = result.filter(
        pl.col("activity_type").eq(ActivityType.unknown)
        | pl.col("cluster_title").is_null()
        | pl.col("cluster_summary").is_null()
        | pl.col("is_sensitive").is_null()
        | pl.col("social_likelihood").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="cluster_label", how="anti").drop(
        ["conversations"]
    )

    # if config.debug:
    #     return result, debug_dataframe
    # else:
    #   return result

    # Columns: date, interests, interests_uniqueness, cluster_label, cluster_title, cluster_summary, is_sensitive, social_likelihood
    return result
