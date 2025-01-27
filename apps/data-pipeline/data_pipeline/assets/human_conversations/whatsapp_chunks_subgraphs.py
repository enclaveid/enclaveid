from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_messaging_partners import get_messaging_partners
from data_pipeline.utils.polars_expressions.messages_struct_to_string_format_expr import (
    get_messages_struct_to_string_format_expr,
)


def _get_subgraph_parsing_prompt(user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
        Format your response in JSON as follows:
        - If a claim contains causal context, break it up into separate claims and link them with the "because" field
        - If a claim involves both users at the same time, assign it to the most relevant user
        - Generate a unique ID for each claim based on the claim content
        - Include the datetime of the claim in YYYY-MM-DD HH:MM:SS format, or just YYYY-MM-DD if the time is ambiguous

        For example, given the claims:
        (without context): {user_name}'s personal trainer texted them today
        (with causal context): {partner_name} has more energy in the mornings, because: {partner_name} is avoiding sugar in the mornings, {partner_name} is eating protein every day

        Your response should be:
        {[
            {
                "id": "trainer_texted",
                "datetime": "...",
                "claim": "{user_name}'s personal trainer texted them today",
                "user": "{user_name}"
            },
            {
                "id": "is_avoiding_sugar_in_the_mornings",
                "datetime": "...",
                "claim": "{partner_name} is avoiding sugar in the mornings",
                "user": "{partner_name}",
            },
            {
                "id": "is_eating_protein_every_day",
                "datetime": "...",
                "claim": "{partner_name} is eating protein every day",
                "user": "{partner_name}",
            },
            {
                "id": "has_more_energy_in_the_mornings",
                "datetime": "...",
                "claim": "{partner_name} has more energy in the mornings",
                "user": "{partner_name}",
                "because": ["is_avoiding_sugar_in_the_mornings", "is_eating_protein_every_day"]
            }
        ]}
        """
    ).strip()


def _get_example_input(user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
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
        """
    ).strip()


IMPORTANT_CONSTRAINTS = """
IMPORTANT:
- The claims MUST be contextually complete: if the context explains what caused the claim, you have to include it in the claim
- If a claim involves both users, both their names must be present in the claim
- Avoids restating the raw message content verbatim
"""


def _get_observables_extraction_prompt_sequence(
    text: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, extract an explicit causal chain of "observable" claims about them.

            Include only claims that are:
            - Directly evident in their words or behavior (like reviewing security camera footage—just stating what’s visible).
            - Accurate and observable without guessing or adding interpretation.
            - Agreed upon by any neutral observer, requiring no assumptions beyond what is plainly stated.

            {_get_example_input(user_name, partner_name)}

            You should extract the following claims:
            - {user_name} wonders if his suggestion helped {partner_name}, because: {user_name} suggested that they drink Kefir in the mornings
            - {partner_name} has more energy in the mornings, because: {partner_name} is avoiding sugar in the mornings, {partner_name} is eating protein every day # NB: more than one cause
            - {partner_name} is eating Kefir in the mornings, because: {user_name} suggested that they drinks Kefir in the mornings
            - {partner_name} will organise their gym routine to go twice a week, because: {partner_name}'s personal trainer texted them today
            - {partner_name} is avoiding sugar in the mornings # NB: no explicit causal context in the data
            - {partner_name} is eating protein every day # NB: no explicit causal context in the data

            {IMPORTANT_CONSTRAINTS}

            Here is the conversation:
            {text}
            """
        ).strip(),
        _get_subgraph_parsing_prompt(user_name, partner_name),
    ]


def _get_inferrables_extraction_prompt_sequence(
    text: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given this chat conversation between {user_name} and {partner_name}, extract an explicit causal chain of "inferrable" claims about them.

            Limit your response to reasonable conclusions based on the evidence:
            - Avoid making basic claims that are already evident in the data
            - Like a detective connecting pieces of evidence
            - Requires domain expertise to make logical connections
            - Most qualified observers would reach similar conclusions
            - Do not use hypothetical language

            {_get_example_input(user_name, partner_name)}

            You should extract the following claims:
            - {partner_name} is going beyond {user_name}'s health suggestions, because: {partner_name} is eating protein every day, {partner_name} is avoiding sugar in the mornings #NB: more than one cause
            - {partner_name} is eager to share progress with {user_name}, because: {partner_name} is enthusiastic and positive about changes in their health
            - {partner_name} trust and openness to {user_name}'s advice, because: {partner_name} values {user_name} suggestions
            - {user_name} is eager to help {partner_name} achieve their health goals, because: {user_name} is supportive of {partner_name}'s health goals

            {IMPORTANT_CONSTRAINTS}

            Here is the conversation:
            {text}
            """
        ).strip(),
        _get_subgraph_parsing_prompt(user_name, partner_name),
    ]


def parse_subgraphs(response: str) -> list[dict] | None:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, list):
            return res
        else:
            return None
    except Exception:
        return None


class WhatsappChunksSubgraphsConfig(RowLimitConfig):
    row_limit: int | None = 3 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_rechunked": AssetIn(
            key=["whatsapp_conversation_rechunked"],
        ),
    },
)
def whatsapp_chunks_subgraphs(
    context: AssetExecutionContext,
    whatsapp_conversation_rechunked: pl.DataFrame,
    deepseek_r1: BaseLlmResource,
    config: WhatsappChunksSubgraphsConfig,
):
    llm = deepseek_r1
    messaging_partners = get_messaging_partners()

    df = whatsapp_conversation_rechunked.with_columns(
        messages_str=get_messages_struct_to_string_format_expr(messaging_partners)
    ).slice(0, config.row_limit)

    observables_prompt_sequences = [
        _get_observables_extraction_prompt_sequence(
            messages_str, messaging_partners.me, messaging_partners.partner
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    (
        observables_completions,
        observables_cost,
    ) = llm.get_prompt_sequences_completions_batch(
        observables_prompt_sequences,
    )

    context.log.info(f"Observables extraction cost: ${observables_cost:.6f}")

    (
        observables_subgraphs,
        observables_raw_analysis,
    ) = zip(
        *[
            (
                parse_subgraphs(completion[-1]),
                completion[-2],
            )
            if completion
            else (None, None)
            for completion in observables_completions
        ]
    )

    inferrables_prompt_sequences = [
        _get_inferrables_extraction_prompt_sequence(
            messages_str, messaging_partners.me, messaging_partners.partner
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    (
        inferrables_completions,
        inferrables_cost,
    ) = llm.get_prompt_sequences_completions_batch(
        inferrables_prompt_sequences,
    )

    context.log.info(f"Inferrables extraction cost: ${inferrables_cost:.6f}")

    (
        inferrables_subgraphs,
        inferrables_raw_analysis,
    ) = zip(
        *[
            (
                parse_subgraphs(completion[-1]),
                completion[-2],
            )
            if completion
            else (None, None)
            for completion in inferrables_completions
        ]
    )

    return df.with_columns(
        observables_subgraph=pl.Series(observables_subgraphs, strict=False),
        observables_raw_analysis=pl.Series(observables_raw_analysis),
        inferrables_subgraph=pl.Series(inferrables_subgraphs, strict=False),
        inferrables_raw_analysis=pl.Series(inferrables_raw_analysis),
    )
