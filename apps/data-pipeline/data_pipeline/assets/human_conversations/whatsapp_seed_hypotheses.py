from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def _get_hypothesis_generation_prompt_sequence(text: str) -> PromptSequence:
    return [
        dedent(
            f"""
            You will be given a problematic chunk of a WhatsApp conversation between two romantic partners.
            Try to formulate an encompassing hypothesis at the root of the misunderstanding, which will be validated later.
            
            Conclude your response with the following JSON format:
            {{
                "hypothesis": "<the hypothesis>"
            }}

            Here is the chunk in question:
            {text}
            """
        ).strip(),
    ]


def _parse_hypothesis(completion: str) -> str | None:
    try:
        res = repair_json(completion, return_objects=True)
        if not isinstance(res, dict):
            return None
        return res["hypothesis"]
    except Exception:
        return None


class WhatsappSeedHypothesesConfig(RowLimitConfig):
    max_hypotheses: int = Field(
        default=5, description="The number of hypotheses to generate"
    )
    sentiment_threshold: float = Field(
        default=-0.3, description="The threshold for the sentiment of the hypotheses"
    )


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_subgraphs": AssetIn(
            key=["whatsapp_chunks_subgraphs"],
        ),
    },
)
def whatsapp_seed_hypotheses(
    context: AssetExecutionContext,
    config: WhatsappSeedHypothesesConfig,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    deepseek_r1: BaseLlmResource,
):
    df = (
        whatsapp_chunks_subgraphs.filter(
            pl.col("sentiment").le(config.sentiment_threshold)
        )
        .sort("sentiment")
        .slice(0, config.max_hypotheses)
    )

    prompt_sequences = [
        _get_hypothesis_generation_prompt_sequence(row["messages_str"])
        for row in df.iter_rows(named=True)
    ]

    completions, cost = deepseek_r1.get_prompt_sequences_completions_batch(
        prompt_sequences
    )

    context.log.info(f"Cost: ${cost:.6f}")

    hypotheses = [
        _parse_hypothesis(completion[-1]) if completion else None
        for completion in completions
    ]

    return df.with_columns(pl.Series(name="hypothesis", values=hypotheses))
