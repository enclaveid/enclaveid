from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.cost_tracker_resource import CostTrackerResource
from data_pipeline.resources.llm_inference.llama70b_resource import Llama70bResource

from ...partitions import user_partitions_def
from ...utils.search_history_utils import (
    parse_classification_result,
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
            """
            Summarize the reactive search activity by taking into account the time periods
            and what the user will have obtained at the end of their search. Describe:

            - The main category of reactive needs
            - The specific types of occasions or needs
            - Frequency pattern of these needs
            - User's apparent level of experience in addressing these needs
            - Any unique elements in the user's approach
            """
        ),
        "proactive": dedent(
            """
            Summarize the knowledge progression by taking into account the time periods and how each
            incremental chunk expands the user's knowledge horizontally or vertically. Describe:

            - The main topic or starting point of interest
            - Key areas or subtopics the user explored from this starting point
            - How the user's understanding seemed to deepen or branch out in each area
            - Any connections or jumps between different areas of exploration
            - The most advanced or recent concepts the user has searched for

            Conclude with the overall trajectory and breadth of the user's learning path.
            """
        ),
    }[parse_classification_result(cluster_classification)[0]],
    dedent(
        """
        Provide a descriptive title for the summary.
        Avoid using generic terms like 'Summary' or 'Analysis' and instead focus on the main theme or outcome of the search activity.
        Do not output any additional text other than the title.
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
    op_tags={"dagster/concurrency_key": "llama70b"},
)
async def cluster_summaries(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    llama70b: Llama70bResource,
    cost_tracker: CostTrackerResource,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
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
    )

    prompt_sequences = [
        [
            summarization_prompt_sequence[0](row["cluster_items"]),
            summarization_prompt_sequence[1],
            summarization_prompt_sequence[2],
        ]
        for row in df.to_dicts()
    ]

    context.log.info(f"Processing {len(prompt_sequences)} clusters...")
    summaries_completions, cost = await llama70b.get_prompt_sequences_completions(
        prompt_sequences
    )

    cost_tracker.log_cost(cost, context)

    cluster_splits = list(
        map(lambda x: x[0] if len(x) > 0 else None, summaries_completions)
    )

    # Tag the clusters with the type of activity: reactive, proactive
    activity_types = []
    sensitivities = []
    for cluster_split in cluster_splits:
        if cluster_split is None:
            activity_types.append("unknown")
        else:
            activity_type, is_sensitive = parse_classification_result(cluster_split)
            activity_types.append(activity_type)
            sensitivities.append(is_sensitive)

    cluster_summaries = list(
        map(lambda x: x[1] if len(x) > 0 else None, summaries_completions)
    )

    cluster_titles = list(
        map(lambda x: x[2] if len(x) > 0 else None, summaries_completions)
    )
    return (
        df.with_columns(
            cluster_dates=df["cluster_dates"],
            cluster_title=pl.Series(cluster_titles),
            cluster_summary=pl.Series(cluster_summaries),
            activity_type=pl.Series(activity_types),
            is_sensitive=pl.Series(sensitivities),
        )
        .filter(pl.col("activity_type") != "unknown")
        .drop(["date_interests", "date", "interests"])
    )
