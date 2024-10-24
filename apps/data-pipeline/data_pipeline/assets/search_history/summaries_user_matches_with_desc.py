from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.parsing.regex import parse_cluster_summarization

from ...constants.custom_config import RowLimitConfig
from ...partitions import user_partitions_def


class UserMatchesSummariesConfig(RowLimitConfig):
    similarity_threshold: float = Field(
        default=0.85,
        description="The threshold of cosine similarity over which to generate a summary for the match.",
    )
    social_likelihood_threshold: float = Field(
        default=0.6,
        description=dedent(
            """
            The threshold of social likelihood over which to generate a summary for the match.
            This is calculated as the average of the two users' social likelihoods.
            """
        ),
    )
    similarities_summarization_prompt: str = Field(
        default=dedent(
            """
            Here are two sequences of search activities around a given topic belonging
            to two different people. What can you tell of the commonalities and
            differences between the two people? Focus on the most striking differences
            and niche similarities. If the match is unique and unlikely, make sure to
            mention it in the conclusion.

            Finally, provide a short title that captures the most important similarities.

            Format your response as follows:
            Title: [Title]
            Summary: [Your summary]
            """
        )
        .replace("\n", " ")
        .strip(),
        description="The prompt to use for summarizing the similarities between the user and the matched user.",
    )
    means_of_comparison: str = Field(
        default="items",
        description="The means of comparison between the two users. Can be either 'items' or 'summaries'.",
    )
    max_summaries_per_user: int = Field(
        default=50,
        description="The maximum number of summaries to generate per user.",
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "summaries_user_matches": AssetIn(key=["summaries_user_matches"]),
        "summaries_interests_matches": AssetIn(key=["summaries_interests_matches"]),
    },
)
async def summaries_user_matches_with_desc(
    context: AssetExecutionContext,
    config: UserMatchesSummariesConfig,
    llama405b: BaseLlmResource,
    summaries_user_matches: pl.DataFrame,
    summaries_interests_matches: pl.DataFrame,
) -> pl.DataFrame | None:
    if summaries_user_matches.is_empty():
        return None

    # Sort by group keys
    summaries_user_matches = summaries_user_matches.with_columns(
        avg_social_likelihood=pl.col("social_likelihoods").apply(lambda x: sum(x) / 2),
    ).sort(
        by=["other_user_id", "cosine_similarity", "avg_social_likelihood"],
        descending=True,
    )

    # Mask summaries that are too dissimilar or too low in social likelihood
    filtered_summaries_user_matches = summaries_user_matches.with_columns(
        mask1=(
            (pl.col("cosine_similarity") < config.similarity_threshold)
            | (pl.col("avg_social_likelihood") < config.social_likelihood_threshold)
        ),
        # Mask summaries that are over the max number of summaries per user
    ).with_columns(
        mask2=(
            pl.int_range(pl.len()).over(["other_user_id", "mask1"])
            >= config.max_summaries_per_user
        )
    )

    context.log.info(
        f"""
        Summarizing {
            filtered_summaries_user_matches.filter(
                pl.col("mask1").not_() & pl.col("mask2").not_()
            )
            .group_by("other_user_id")
            .agg(pl.count())
            .to_dicts()
        } matches out of {
          summaries_user_matches.group_by("other_user_id").agg(pl.count()).to_dicts()
        }."""
    )

    means_of_comparison = f"common_summary_prompt_{config.means_of_comparison}"

    (
        summaries_completions,
        cost,
    ) = llama405b.get_prompt_sequences_completions_batch(
        list(
            map(
                lambda x: [
                    f"{config.similarities_summarization_prompt}\n{x[means_of_comparison]}"
                ]
                if not x["mask1"] and not x["mask2"]
                else [],
                filtered_summaries_user_matches.to_dicts(),
            )
        )
    )

    context.log.info(f"Execution cost: ${cost:.2f}")

    common_titles, common_summaries = zip(
        *[
            parse_cluster_summarization(x[0]) if len(x) > 0 else (None, None)
            for x in summaries_completions
        ]
    )

    return summaries_user_matches.with_columns(
        common_summary=pl.Series(common_summaries),
        common_title=pl.Series(common_titles),
    ).drop(
        [
            "common_summary_prompt_summaries",
            "common_summary_prompt_items",
        ]
    )
