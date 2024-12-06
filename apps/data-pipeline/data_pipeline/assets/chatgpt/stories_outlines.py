from textwrap import dedent
from typing import cast

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import repair_json


def parse_story_outline_json(text: str) -> tuple[list[dict] | None, list[dict] | None]:
    """Parse the story outline JSON response from the LLM.

    Args:
        text: Raw text response from LLM containing JSON

    Returns:
        Tuple of (emotional_anchors, transitions) where each is a list of dicts
        with 'description' and 'grounding' keys, or (None, None) if parsing fails
    """
    try:
        j = cast(dict, repair_json(text, return_objects=True))
        emotional_anchors = j.get("emotional_anchors")
        transitions = j.get("transitions")

        # Validate structure
        if emotional_anchors:
            for anchor in emotional_anchors:
                if not isinstance(anchor.get("description"), str):
                    return None, None
                if anchor.get("grounding") not in [
                    "grounded",
                    "inferred",
                    "speculative",
                ]:
                    return None, None

        if transitions:
            for transition in transitions:
                if not isinstance(transition.get("description"), str):
                    return None, None
                if transition.get("grounding") not in [
                    "grounded",
                    "inferred",
                    "speculative",
                ]:
                    return None, None

        return emotional_anchors, transitions

    except Exception:
        return None, None


def get_story_outline_prompt(
    fine_cluster_summaries: list[str], personal_details: str | None = None
) -> list[str]:
    summaries_text = "\n\n".join(
        f"fine cluster summary {i+1}:\n{summary}"
        for i, summary in enumerate(fine_cluster_summaries)
    )

    return [
        dedent(
            f"""
            Here is a list of emotional anchors for a given topic of activity for an imaginary character.
            What overarching theme and what character goals/motivations can you infer?

            {summaries_text}
            """
        ).strip(),
        dedent(
            f"""
            What could be the skeleton of a conflict-driven narrative within this overarching theme that pivots on the given emotional anchors?
            It has to be from the perspective of the user whose activity produced such anchors.

            Here are some basic personal details about them:
            {personal_details or "Male in their 20s"}
            """
        ).strip(),
        dedent(
            """
            A narrative of this type can be schematized as a set of emotional states between which the characters transitions by doing practical actions in the real world.
            You've used some of the provided emotional anchors and filled up the transitions with specific behaviors.
            Can you provide two lists containing one the emotional anchors and the other one the transitions you used.
            Also mark the ones which are grounded in the list provided above.

            Format your answer in JSON:
            {
                "emotional_anchors": [{
                    "description": ...,
                    "grounding": "grounded" | "inferred" | "speculative"
                }],
                "transitions": [{
                    "description": ...,
                    "grounding": "grounded" | "inferred" | "speculative"
                }],
            }
            """
        ).strip(),
    ]


# TODO: inject personal details from the user profile
@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversations_clusters_summaries": AssetIn(
            key=["conversations_clusters_summaries"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def stories_outlines(
    context: AssetExecutionContext,
    gemini_flash: BaseLlmResource,
    conversations_clusters_summaries: pl.DataFrame,
) -> pl.DataFrame:
    llm = gemini_flash
    logger = get_logger(context)

    # Group by coarse cluster and filter for emotional clusters
    cluster_emotions = (
        conversations_clusters_summaries.filter(pl.col("is_emotional"))
        .with_columns(
            title_emotions=pl.concat_str(
                [
                    pl.col("start_date"),
                    pl.lit(" - "),
                    pl.col("title"),
                    pl.lit(":\n- "),
                    pl.col("strong_emotional_implications").list.join("\n- "),
                    pl.lit("\n\n"),
                ]
            )
        )
        .group_by("fine_cluster_label", "fine_cluster_summary", "coarse_cluster_label")
        .agg(
            title_emotions=pl.col("title_emotions").str.concat("\n"),
            average_fine_cluster_date=pl.col("start_date").str.to_date().mean(),
        )
        .with_columns(
            cluster_emotions=pl.concat_str(
                [
                    pl.lit("### "),
                    pl.col("fine_cluster_label"),
                    pl.lit(" - "),
                    pl.col("fine_cluster_summary"),
                    pl.lit(":\n\n"),
                    pl.col("title_emotions"),
                ]
            )
        )
        .sort("average_fine_cluster_date")
        .group_by("coarse_cluster_label")
        .agg(
            cluster_emotions=pl.col("cluster_emotions").str.concat("\n"),
            average_coarse_cluster_date=pl.col("average_fine_cluster_date")
            .dt.date()
            .mean(),
        )
        .sort("average_coarse_cluster_date")
    )

    # Generate prompts for each coarse cluster
    prompt_sequences = [
        get_story_outline_prompt(row["cluster_emotions"])
        for row in cluster_emotions.to_dicts()
    ]

    logger.info(
        f"Processing {len(prompt_sequences)} coarse clusters with emotional implications..."
    )
    completions, cost = llm.get_prompt_sequences_completions_batch(prompt_sequences)
    logger.info(f"Story outlines generation cost: ${cost:.2f}")

    # Parse story outlines
    parsed_outlines = [
        (completion[-2].strip(), *parse_story_outline_json(completion[-1].strip()))
        if completion
        else (None, None, None)
        for completion in completions
    ]

    # Unzip the tuples into separate lists
    story_outlines, emotional_anchors, transitions = zip(*parsed_outlines)

    # Add story outlines to results
    result = cluster_emotions.with_columns(
        story_outline=pl.Series(story_outlines),
        emotional_anchors=pl.Series(emotional_anchors),
        transitions=pl.Series(transitions),
    )

    # Join back to original DataFrame to maintain all records
    # final_result = conversations_clusters_summaries.join(
    #     result.select(["coarse_cluster_label", "story_outline"]),
    #     on="coarse_cluster_label",
    #     how="left",
    # )

    return result
