from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_messaging_partners import (
    get_messaging_partners,
)
from data_pipeline.utils.parsing.parse_whatsapp_claims import parse_whatsapp_claims
from data_pipeline.utils.polars_expressions.messages_struct_to_string_format_expr import (
    get_messages_struct_to_string_format_expr,
)


def _get_sentiment_analysis_prompt_sequence(
    text: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, analyze the sentiment of both participants in the conversation.
            The sentiment should be a float between -1 and 1, where -1 is the most negative sentiment and 1 is the most positive sentiment.
            Each sentiment score should be associated with a time range in the conversation, in the format "HH:MM:SS".

            Conclude your analysis with a JSON object with the following structure:
            {{
                "{user_name}": [
                   {{
                    "from": "YYYY-MM-DD HH:MM:SS",
                    "to": "YYYY-MM-DD HH:MM:SS",
                    "sentiment": <float between -1 and 1>
                   }}
                ],
                "{partner_name}": [
                   {{
                    "from": "YYYY-MM-DD HH:MM:SS",
                    "to": "YYYY-MM-DD HH:MM:SS",
                    "sentiment": <float between -1 and 1>
                   }}
                ],
            }}

            Here is the conversation:
            {text}
            """
        ).strip(),
    ]


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_rechunked": AssetIn(
            key=["whatsapp_chunks_rechunked"],
        ),
    },
)
def whatsapp_chunks_sentiment(
    context: AssetExecutionContext,
    config: Config,
    gpt4o: BaseLlmResource,
    whatsapp_chunks_rechunked: pl.DataFrame,
) -> pl.DataFrame:
    messaging_partners = get_messaging_partners()

    df = whatsapp_chunks_rechunked.with_columns(
        messages_str=get_messages_struct_to_string_format_expr(messaging_partners)
    )

    prompt_sequences = [
        _get_sentiment_analysis_prompt_sequence(
            messages_str, messaging_partners.me, messaging_partners.partner
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"Sentiment analysis cost: ${cost:.6f}")

    sentiment_me, sentiment_partner, raw_analysis = zip(
        *[
            (
                *parse_whatsapp_claims(
                    messaging_partners.me, messaging_partners.partner, completion[-1]
                ),
                completion[-1],
            )
            if completion
            else (None, None, None)
            for completion in completions
        ]
    )

    result_df = df.with_columns(
        sentiment_me=pl.Series(sentiment_me, strict=False),
        sentiment_partner=pl.Series(sentiment_partner, strict=False),
        raw_analysis=pl.Series(raw_analysis, strict=False),
    )

    return result_df
