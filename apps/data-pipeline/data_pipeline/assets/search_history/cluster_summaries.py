import time
from datetime import datetime
from enum import Enum
from textwrap import dedent
from typing import List, Tuple, cast

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetOut,
    multi_asset,
)
from pydantic import BaseModel, Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.llm_inference.gemma27b_resource import Gemma27bResource
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger

from ...constants.k8s import k8s_vllm_config
from ...partitions import user_partitions_def


class ActivityType(str, Enum):
    knowledge_progression = "knowledge_progression"
    reactive_needs = "reactive_needs"
    unknown = "unknown"


class InitialClassificationResult(BaseModel):
    activity_type: ActivityType
    sensitive: bool
    explanation: str


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

        Provide a classification as either 'Knowledge Progression' or 'Reactive Needs', along with a confidence score (0-100%).
        Then, offer a brief explanation (2-3 sentences) supporting your classification, highlighting the key factors that influenced your decision.
        Additionally, assess whether the topic is sensitive in nature, particularly regarding psychosocial aspects.

        Format your response in JSON as follows:
        {{
          activity_type: "knowledge_progression" or "reactive_needs" or "unknown",
          sensitive: true or false,
          explanation: "Your 2-3 sentence explanation"
        }}

        {search_activity}
        """
    )


class SummarizationResult(BaseModel):
    title: str
    summary: str


def get_summarization_prompt(
    initial_classification_result: InitialClassificationResult | None
) -> str:
    CLUSTER_SUMMARIZATION_FORMAT = dedent(
        """
        Finally, provide the most detailed possible category that captures all the topics of the activity.

        Format your response in JSON as follows:
        {{
          title: "The category you found",
          summary: "Your summary"
        }}
        """
    )

    return {
        "unknown": None,
        "reactive": dedent(
            f"""
            Summarize the reactive search activity by taking into account the time periods
            and what the user will have obtained at the end of their search. Describe:

            - The main category of reactive needs
            - The specific types of occasions or needs
            - Frequency pattern of these needs
            - User's apparent level of experience in addressing these needs
            - Any unique elements in the user's approach

            {CLUSTER_SUMMARIZATION_FORMAT}
            """
        ),
        "proactive": dedent(
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
    }[
        initial_classification_result.activity_type
        if initial_classification_result
        else "unknown"
    ]


class SocialLikelihoodResult(BaseModel):
    likelihood: int
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

        Provide a social likelihood score from 0 to 100% and format your answer in JSON as follows:
        {{
          likelihood: 0-100,
          explanation: "Your explanation"
        }}
        """
)


class ClusterSummariesConfig(RowLimitConfig):
    debug: bool = Field(
        default=True,
        description="Set to True to materialize the cluster_summaries_debug asset, which includes the full assistant replies.",
    )


@multi_asset(
    partitions_def=user_partitions_def,
    outs={
        "cluster_summaries": AssetOut(
            key=["cluster_summaries"],
            io_manager_key="parquet_io_manager",
            is_required=True,
        ),
        "cluster_summaries_debug": AssetOut(
            key=["cluster_summaries_debug"],
            io_manager_key="parquet_io_manager",
            is_required=False,
        ),
    },
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    op_tags=k8s_vllm_config,
)
async def cluster_summaries(
    context: AssetExecutionContext,
    config: ClusterSummariesConfig,
    gemma27b: Gemma27bResource,
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
        .group_by("cluster_label")
        .agg(
            [
                pl.col("date_interests").str.concat("\n").alias("cluster_items"),
                pl.col("date").sort().alias("cluster_dates"),
            ]
        )
        .filter(pl.col("cluster_label") != -1)
        .slice(0, config.row_limit)
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
        [
            InitialClassificationResult,
            SummarizationResult,
            SocialLikelihoodResult,
        ],
    )
    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    summaries_completions = cast(
        List[
            Tuple[
                InitialClassificationResult, SummarizationResult, SocialLikelihoodResult
            ]
        ],
        summaries_completions,
    )

    results = {
        "activity_type": [],
        "is_sensitive": [],
        "cluster_summary": [],
        "cluster_title": [],
        "social_likelihood": [],
        "conversations": conversations,
    }

    (
        results["activity_type"],
        results["is_sensitive"],
        results["cluster_title"],
        results["cluster_summary"],
        results["social_likelihood"],
    ) = zip(
        *list(
            map(
                lambda x: (
                    x[0].activity_type if x[0] else "unknown",
                    x[0].sensitive if x[0] else None,
                    x[1].title if x[1] else None,
                    x[1].summary if x[1] else None,
                    x[2].likelihood / 100.0 if x[2] else None,
                )
                if x
                else (None, None, None, None, None),
                summaries_completions,
            )
        )
    )

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    result = df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )

    debug_dataframe = result.clone()

    invalid_results = result.filter(
        pl.col("activity_type").eq("unknown")
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

    if config.debug:
        return result, debug_dataframe
    else:
        return result
