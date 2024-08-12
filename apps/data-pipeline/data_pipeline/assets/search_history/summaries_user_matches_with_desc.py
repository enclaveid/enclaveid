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

    summaries_completions = await llama405b.get_prompt_sequences_completions(
        list(
            map(
                lambda x: [x["common_summary_prompt"]]
                if x["cosine_similarity"] > config.similarity_threshold
                else [],
                summaries_user_matches.to_dicts(),
            )
        )
    )

    return summaries_user_matches.with_columns(
        common_summary=pl.Series(
            [x[0] if len(x) > 0 else None for x in summaries_completions]
        )
    ).drop(["common_summary_prompt"])
