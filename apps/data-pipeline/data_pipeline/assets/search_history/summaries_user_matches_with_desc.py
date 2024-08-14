from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.resources.llm_inference.llama405b_resource import Llama405bResource

from ...constants.custom_config import RowLimitConfig
from ...partitions import user_partitions_def


class UserMatchesSummariesConfig(RowLimitConfig):
    similarity_threshold: float = Field(
        default=0.93,
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


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "summaries_user_matches": AssetIn(key=["summaries_user_matches"]),
    },
)
async def summaries_user_matches_with_desc(
    context: AssetExecutionContext,
    config: UserMatchesSummariesConfig,
    llama405b: Llama405bResource,
    summaries_user_matches: pl.DataFrame,
) -> pl.DataFrame:
    context.log.info(
        f"Summarizing {len(summaries_user_matches.filter(pl.col('cosine_similarity') > config.similarity_threshold))} matches."
    )

    means_of_comparison = f"common_summary_prompt_{config.means_of_comparison}"

    summaries_completions, cost = await llama405b.get_prompt_sequences_completions(
        list(
            map(
                lambda x: [
                    f"{config.similarities_summarization_prompt}\n{x[means_of_comparison]}"
                ]
                if (
                    x["cosine_similarity"] > config.similarity_threshold
                    and (
                        (sum(x["social_likelihoods"]) / 2)
                        > config.social_likelihood_threshold
                    )
                )
                else [],
                summaries_user_matches.to_dicts(),
            )
        )
    )

    context.log.info(f"Execution cost: ${cost:.2f}")

    return summaries_user_matches.with_columns(
        common_summary=pl.Series(
            [x[0] if len(x) > 0 else None for x in summaries_completions]
        )
    ).drop(
        [
            "common_summary_prompt_summaries",
            "common_summary_prompt_items",
        ]
    )
