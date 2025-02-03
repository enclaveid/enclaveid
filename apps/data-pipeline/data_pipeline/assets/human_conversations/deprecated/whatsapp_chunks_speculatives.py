from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.constants.whatsapp_conversations import PartnerType
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
from data_pipeline.utils.speculative_hypotheses_guidance import (
    get_speculative_hypotheses_guidance,
)


def _get_json_formatting_prompt(user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
          Format your previous response as a JSON object with the following schema:

          {{
            "{user_name}": [
              "Description of speculation 1",
              "Description of speculation 2",
              ...
            ],
            "{partner_name}": [
              "Description of speculation 1",
              "Description of speculation 2",
              ...
            ]
          }}

          IMPORTANT:
          - If a claim involves both users, both their names must be present in the claim description!
          - If a claim involves both users at the same time, assign it to the most relevant user.
        """
    ).strip()


def _get_speculatives_extraction_prompt_sequence(
    text: str, user_name: str, partner_name: str, partner_type: PartnerType
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, come up with a list of speculations about the users' deeper motivations and/or circumstances.

            Rules:
            - Consider all possible factors: psychological, social, environmental, technological, economic, cultural, etc.
            - Prioritize insight over certainty as each speculation will be validated individually at a later stage
            - Do not use hypothetical language in the speculations
            - Each speculation should be a standalone statement without referencing the original behaviors verbatim.

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

            You could extract the following claims:
            - {partner_name} desires to please {user_name} or gain their approval.
            - {partner_name} is reshaping their fitness habits due to an underlying health issue (e.g., pre-diabetes, weight concerns, or chronic fatigue).
            - {partner_name} is attempting to deepen the bond with {user_name} by sharing personal details and experiences.
            - {partner_name} values {user_name}'s opinion and is using health changes as a way to stay close or create a sense of shared journey.
            - {user_name} has experience with health and nutrition, having gone through a similar health journey as {partner_name}.
            - {partner_name} shifts in diet and exercise habits are driven by stress or a recent life change—such as a breakup, job change, or mental-health struggles.
            - {partner_name} is using fitness and nutrition as a way to regain control or manage emotions.

            IMPORTANT:
            {get_speculative_hypotheses_guidance(partner_type)}

            Here is the conversation:
            {text}
            """
        ).strip(),
        _get_json_formatting_prompt(user_name, partner_name),
    ]


@asset(
    partitions_def=partitions,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_rechunked": AssetIn(
            key=["whatsapp_conversation_rechunked"],
        ),
    },
)
def whatsapp_chunks_speculatives(
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
        _get_speculatives_extraction_prompt_sequence(
            messages_str,
            messaging_partners.me,
            messaging_partners.partner,
            messaging_partners.partner_type,
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"speculatives extraction cost: ${cost:.6f}")

    speculatives_me, speculatives_partner, raw_analysis = zip(
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
        speculatives_me=pl.Series(speculatives_me),
        speculatives_partner=pl.Series(speculatives_partner),
        raw_analysis=pl.Series(raw_analysis),
    )
    return result_df
