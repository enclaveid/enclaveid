import time
from datetime import datetime
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.llm_inference.gemma27b_resource import Gemma27bResource
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger

from ...constants.k8s import k8s_vllm_config
from ...partitions import user_partitions_def
from ...utils.search_history_utils import (
    parse_classification_result,
    parse_cluster_summarization,
)

CLUSTER_CLASSIFICATION_FORMAT = dedent(
    """
    Finally, provide the most detailed possible category that captures all the topics of the activity.

    Format your response as follows:
    Title: [The category you found]
    Summary: [Your summary]
    """
)

summarization_prompt_sequence = [
    lambda search_activity: dedent(
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

        Format your response as follows:
        Classification: [Knowledge Progression/Reactive Needs]
        Confidence: [0-100%]
        Sensitive: [true/false]
        Explanation: [Your 2-3 sentence explanation]

        {search_activity}
        """
    ),
    lambda cluster_classification: {
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

            {CLUSTER_CLASSIFICATION_FORMAT}
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

            {CLUSTER_CLASSIFICATION_FORMAT}
            """
        ),
    }[parse_classification_result(cluster_classification)[0]],
    dedent(
        f"""
        Would this type of activity be interesting to connect over with other similar users?
        In your analysis, take into account:
        - [IMPORTANT] Whether the topic itself is generally boring (e.g., main job, taxation, laundry) or engaging (e.g., arts, games, hobbies)
        - How deeply engaged the user seems to be with the topic
        - Whether the user engaged in very niche areas of the topic
        - If the activity is sensitive, assume the user is willing to share it with others
        - The current date is {datetime.today().strftime('%Y-%m-%d')}, if the activity is reactive, consider that it might not be relevant for the user if they did it long ago

        At the end of your analysis, provide a social likelihood score from 0 to 100%, formatted as follows:
        Likelihood: [0-100%]
        """
    ),
]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    op_tags=k8s_vllm_config,
)
async def cluster_summaries(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    gemma27b: Gemma27bResource,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    logger = get_logger(context)

    df = (
        interests_clusters.sort(by=pl.col("date"))
        .with_columns(
            (pl.col("date") + pl.lit(":") + pl.col("interests")).alias("date_interests")
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
            summarization_prompt_sequence[0](row["cluster_items"]),
            summarization_prompt_sequence[1],
            summarization_prompt_sequence[2],
        ]
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} clusters...")
    summaries_completions = gemma27b.get_prompt_sequences_completions_batch(
        prompt_sequences
    )

    logger.info(f"Done processing {len(prompt_sequences)} clusters.")

    results = {
        "activity_type": [],
        "is_sensitive": [],
        "cluster_summary": [],
        "cluster_title": [],
        "social_likelihood": [],
    }

    cluster_splits = list(
        map(lambda x: x[0] if len(x) > 0 else None, summaries_completions)
    )

    # Tag the clusters with the type of activity: reactive, proactive
    for cluster_split in cluster_splits:
        if cluster_split is None:
            results["activity_type"].append("unknown")
        else:
            activity_type, is_sensitive = parse_classification_result(cluster_split)
            results["activity_type"].append(activity_type)
            results["is_sensitive"].append(is_sensitive)

    results["cluster_title"], results["cluster_summary"] = zip(
        *list(
            map(
                lambda x: parse_cluster_summarization(x[1]) if len(x) > 0 else None,
                summaries_completions,
            )
        )
    )

    results["social_likelihood"] = list(
        map(lambda x: x[2] if len(x) > 0 else None, summaries_completions)
    )

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    return df.hstack(pl.DataFrame(results)).drop(
        ["date_interests", "date", "interests"]
    )
