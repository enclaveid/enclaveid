import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def _get_sentiment_prompt_sequence(text: str) -> PromptSequence:
    return [
        f"""
        Analyze whether this proposition has positive, negative or neutral implications for the user(s) involved.
        Return a number between -1 and 1, where -1 is negative, 0 is neutral, and 1 is positive.

        Use this JSON format:
        {{
            "sentiment": "the sentiment value as a float between -1 and 1 without quotes"
        }}

        Here is the proposition: {text}
        """
    ]


def _parse_sentiment_response(response: str) -> float | None:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, dict):
            return res["sentiment"]
        else:
            return None
    except Exception:
        return None


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_nodes_deduplicated": AssetIn(
            key=["whatsapp_nodes_deduplicated"],
        ),
    },
)
async def whatsapp_node_sentiments(
    context: AssetExecutionContext,
    whatsapp_nodes_deduplicated: pl.DataFrame,
    llama70b: BaseLlmResource,
) -> pl.DataFrame:
    df = whatsapp_nodes_deduplicated

    prompt_sequences = [
        _get_sentiment_prompt_sequence(proposition)
        for proposition in df.get_column("proposition").to_list()
    ]

    completions, cost = llama70b.get_prompt_sequences_completions_batch(
        prompt_sequences
    )

    context.log.info(f"Cost: ${cost:.6f}")

    sentiments = [
        _parse_sentiment_response(completion[-1]) if completion else None
        for completion in completions
    ]

    return df.with_columns(
        pl.Series(name="sentiment", values=sentiments).fill_nan(0).fill_null(0)
    )
