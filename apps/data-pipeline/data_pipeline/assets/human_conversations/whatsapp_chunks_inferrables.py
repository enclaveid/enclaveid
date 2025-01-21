from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
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


def _get_json_formatting_prompt(user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
          Format your previous response as a JSON object with the following schema:

          {{
            "{user_name}": [
              "Description of claim 1",
              "Description of claim 2",
              ...
            ],
            "{partner_name}": [
              "Description of claim 1",
              "Description of claim 2",
              ...
            ]
          }}

          If a claim involves both users at the same time, assign it to the most relevant user.
        """
    ).strip()


def _get_inferrables_extraction_prompt_sequence(
    text: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, extract "inferrable" claims about them.

            Limit your response to reasonable conclusions based on the evidence:
            - Like a detective connecting pieces of evidence
            - Requires domain expertise to make logical connections
            - Most qualified observers would reach similar conclusions
            - Add synthesized meaning beyond just restating behaviors
            - Do not use hypothetical language

            For example, given this input:
            - From {partner_name} to {user_name}: "Sent 2 of MEDIA: IMAGE"
            - From {user_name} to {partner_name}: "Kefir!"
            - From {partner_name} to {user_name}: "Yea, since you told me I drink it in the mornings"
            - From {user_name} to {partner_name}: "does it help?"
            - From {partner_name} to {user_name}: "I have more energy in the mornings"
            - From {partner_name} to {user_name}: "I don’t eat sugar anymore in the mornings"
            - From {partner_name} to {user_name}: "I’m eating protein every day"
            - From {partner_name} to {user_name}: "And my personal trainer texted me today so I’ll organise my routine to go twice a week"
            - From {partner_name} to {user_name}: "💪🏼💪🏼"

            You should extract the following claims:
            - {partner_name} attributes having “more energy” in the mornings due to avoiding sugar, eating protein, and drinking Kefir
            - {partner_name} is following {user_name}'s dietary suggestions and seeing results
            - {partner_name} is organising a new of improved gym routine to go twice a week
            - {partner_name} is enthusiastic and positive about changes in their health and is eager to share progress with {user_name}
            - {partner_name} values {user_name}'s health suggestions, indicating trust and openness to their advice
            - {user_name} is supportive of {partner_name}'s health goals and is eager to help them achieve them

            Note how the claims are:
            - Presenting conclusions as independently formed insights rather than summaries
            - High confidence and coherent, with only one valid interpretation across them
            - Standalone statements without referencing the original behaviors they are based on

            IMPORTANT: If a claim involves both users, both their names must be present in the claim!

            Here is the conversation:
            {text}
            """
        ).strip(),
        _get_json_formatting_prompt(user_name, partner_name),
    ]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_rechunked": AssetIn(
            key=["whatsapp_conversation_rechunked"],
        ),
    },
)
def whatsapp_chunks_inferrables(
    context: AssetExecutionContext,
    config: Config,
    gpt4o: BaseLlmResource,
    whatsapp_conversation_rechunked: pl.DataFrame,
) -> pl.DataFrame:
    messaging_partners = get_messaging_partners()

    df = whatsapp_conversation_rechunked.with_columns(
        messages_str=get_messages_struct_to_string_format_expr(messaging_partners)
    )

    prompt_sequences = [
        _get_inferrables_extraction_prompt_sequence(
            messages_str, messaging_partners.me, messaging_partners.partner
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"inferrables extraction cost: ${cost:.6f}")

    inferrables_me, inferrables_partner, raw_analysis = zip(
        *[
            (
                *parse_whatsapp_claims(
                    messaging_partners.me, messaging_partners.partner, completion[-1]
                ),
                completion[-2],
            )
            if completion
            else (None, None, None)
            for completion in completions
        ]
    )

    result_df = df.with_columns(
        inferrables_me=pl.Series(inferrables_me),
        inferrables_partner=pl.Series(inferrables_partner),
        raw_analysis=pl.Series(raw_analysis),
    )
    return result_df
