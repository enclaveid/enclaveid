from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_messaging_partner_name import (
    get_messaging_partners_names,
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
              {{
                "datetime": "YYYY-MM-DD HH:MM:SS",
                "claim": "description of the claim"
              }},
              ...
            ],
            "{partner_name}": [
              {{
                "datetime": "YYYY-MM-DD HH:MM:SS",
                "claim": "description of the claim"
              }},
              ...
            ]
          }}

          If a claim involves both users at the same time, assign it to the most relevant user.
        """
    ).strip()


def _get_observables_extraction_prompt_sequence(
    text: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, extract "observable" claims about them.

            Include only claims that are:
            - Directly evident in their words or behavior (like reviewing security camera footage—just stating what’s visible).
            - Accurate and observable without guessing or adding interpretation.
            - Agreed upon by any neutral observer, requiring no assumptions beyond what is plainly stated.

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
            - {user_name} suggested that {partner_name} drinks Kefir in the mornings
            - {user_name} wonders if his suggestion of drinking Kefir in the mornings helped {partner_name}
            - {partner_name} has more energy in the mornings due to {user_name}'s suggestions
            - {partner_name} is avoiding sugar in the mornings
            - {partner_name} is eating protein every day
            - {partner_name}'s personal trainer texted them today so they'll organise their gym routine to go twice a week

            Note how each claim is:
            - Contextually complete, can be red independently while still delivering complete information.
            - High confidence and descriptive, without additional assumptions
            - Avoids restating the raw message content verbatim

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
def whatsapp_chunks_observables(
    context: AssetExecutionContext,
    config: Config,
    gpt4o: BaseLlmResource,
    whatsapp_conversation_rechunked: pl.DataFrame,
) -> pl.DataFrame:
    partner_names = get_messaging_partners_names()

    df = whatsapp_conversation_rechunked.with_columns(
        messages_str=get_messages_struct_to_string_format_expr(partner_names)
    )

    prompt_sequences = [
        _get_observables_extraction_prompt_sequence(
            messages_str, partner_names["me"], partner_names["partner"]
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"Observables extraction cost: ${cost:.6f}")

    observables_me, observables_partner, raw_analysis = zip(
        *[
            (
                *parse_whatsapp_claims(
                    partner_names["me"], partner_names["partner"], completion[-1]
                ),
                completion[-2],
            )
            if completion
            else (None, None, None)
            for completion in completions
        ]
    )

    result_df = df.with_columns(
        observables_me=pl.Series(observables_me),
        observables_partner=pl.Series(observables_partner),
        raw_analysis=pl.Series(raw_analysis),
    )
    return result_df
