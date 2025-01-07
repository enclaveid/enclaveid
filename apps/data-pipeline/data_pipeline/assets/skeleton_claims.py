from textwrap import dedent
from typing import Callable

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import (
    get_environment,
)
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def get_observables_extraction_prompt_sequence(text: str) -> PromptSequence:
    return [
        dedent(
            f"""
          Given this Q&A conversation between a person and an AI, extract a list of contextually complete facts about the user.
          Limit your response to facts that are directly evident in their behavior and require no inference beyond the evidence:
          - Like reviewing security camera footage - simply stating what's there
          - Requires no interpretation, just accurate description
          - Any observer would agree on these facts

          For example:

          Input 1:
          Q: are there any fully online accredited computer science degrees?
          A: Listed several US universities offering fully online, accredited computer science bachelor's and master's degrees
          Q: are there any fully online accredited computer science bachelor degrees in europe which are transfer-friendly? can you also report their annual tuition fees?
          A: Mentioned the University of London (via Coursera), University of Liverpool, and Open University as potential options, noting that transferability varies and tuition fees should be verified directly with the universities.
          Q: what is the cheapest/easiest to get into of any such programs you mentioned?
          A: Suggested the University of London's Coursera program as a potentially cheaper option, but cautioned that "easiest" is subjective. Outlined the admission requirements for the University of London program, including options for students who don't meet traditional requirements, and emphasized that these requirements and the definition of "easiest" may have changed.

          Output 1:
          - The user asked about fully online accredited computer science degrees, first generally and then specifically about European programs.
          - The user inquired about transfer-friendly programs and their tuition fees.
          - The user specifically asked which of the mentioned programs was the cheapest and easiest to get into.

          Input 2:
          Q: Why did democracy with universal suffrage become the political system of modern societies although most people are not educated enough to make the right electoral decisions? A: Democracy is rooted in the principle of equality, granting everyone a voice regardless of education level. While not everyone is equally informed, democracy values representation and inclusivity, acknowledging the subjectivity of "right" decisions. It aims for a fair process, not necessarily perfect outcomes, and often invests in civic education to improve decision-making.
          Q: Shouldn’t we start prioritizing making the right decision rather than making the process fair? A: Defining "right decisions" and who decides them presents challenges. Prioritizing "right" decisions over fairness risks creating an oligarchy or autocracy, excluding certain perspectives and potentially benefiting a select few. While reforms like deliberative democracy and technocracy exist, finding a balance between informed decision-making and inclusivity remains crucial.

          Output 2:
          - The user argues that most people are not educated enough to make correct electoral decisions in a democracy with universal suffrage.
          - The user wonders if making correct decisions should be prioritized over ensuring a fair process in a democratic system.
          - The user argues that there are objectively "right" electoral decisions that can be determined.

          Note how:
          - Each fact is contextually complete, can be red independently while still delivering complete information.
          - The claims are high confidence and descriptive, without additional assumptions

          Here is the conversation:
          {text}
        """
        ).strip(),
        get_json_formatting_prompt(with_time=True),
    ]


def get_inferrables_extraction_prompt_sequence(text: str) -> PromptSequence:
    return [
        dedent(
            f"""
          Given the following list of behavioral claims about a user for a topical sequence of actions, extract a list of contextually complete facts about the user that are most likely to have caused those actions.
          Limit your response to reasonable conclusions based on the evidence:
          - Like a detective connecting pieces of evidence
          - Requires domain expertise to make logical connections
          - Most qualified observers would reach similar conclusions
          - Add synthesized meaning beyond just restating behaviors
          - Do not use hypothetical language
          Format each fact as a standalone statement without referencing the original behaviors it is based on.

          Example Input:
          - The user needs to take a single general physics exam online and is looking for universities that offer proctored exams for a fee.
          - The user inquired about the National Evaluation Series (NES) as a potential option for taking a physics exam.
          - The user asked about universities that do not require course enrollment to take exams, seeking an exception to the general rule.
          - The user expressed interest in alternatives to traditional university exams, such as CLEP and DSST, that offer college credit via subject exams.
          - The user specifically asked about options available in Italy, seeking information on Italian equivalents to CLEP or DSST, or other alternatives like Coursera/edX courses or International Baccalaureate exams.

          Example Output:
          - The user is either currently located in Italy or planning to be in Italy.
          - The user is pursuing formal academic credit or certification in physics.
          - The user is not affiliated with any academic institution and is acting as an independent learner.
          - The user requires official validation of their physics knowledge through recognized institutions.
          - The user faces institutional or geographic barriers that prevent them from pursuing traditional physics education paths.

          Note how:
          - Each fact is presenting conclusions as independently formed insights rather than summaries
          - The claims are high confidence and coherent, with only one valid interpretation across them

          {text}
        """
        ).strip(),
        get_json_formatting_prompt(),
    ]


def get_speculatives_extraction_prompt_sequence(
    observables_text: str, inferrables_text: str
) -> PromptSequence:
    return [
        dedent(
            f"""
          Given the following list of user behaviors and likely surface causes for those behaviors, come up with a list of speculations about the user's deeper motivations and/or circumstances.

          Rules:
          - Consider all possible factors: psychological, social, environmental, technological, economic, cultural, etc.
          - Prioritize insight over certainty - these will be validated later - and do not use hypothetical language
          - Each speculation should be a standalone statement without referencing the original behaviors or surface causes it is based on.

          Example output:
          NO: The user could be a person who values authenticity and depth in their online interactions, and is seeking to avoid the superficiality or pretentiousness that often characterizes social media conversations, instead opting for more genuine and heartfelt connections.
          YES: The user values authenticity and depth in their online interactions.

          USER BEHAVIORS
          {observables_text}

          SURFACE CAUSES
          {inferrables_text}
        """
        ).strip(),
        get_json_formatting_prompt(),
    ]


def get_causal_relationships_extraction_prompt(
    observables_json: str, inferrables_json: str
) -> str:
    return dedent(
        f"""
          Generate a network of causal relationships between observable behaviors and contributing factors.
          - Create chains of relationships where elements directly influence each other
          - Multiple factors or behaviors can influence a single outcome, but prefer chains over stars
          - Both factors and behaviors can serve as causes
          - Factors can have causal relationships with other factors
          - Behaviors can have causal relationships with other behaviors

          Example of good causal chain combining factors and behaviors:
          NEGATIVE_PAST_EXPERIENCES -> INTENTIONAL_RELATIONSHIP_APPROACH -> WANTS_TO_ASSESS_TRAITS

          IMPORTANT: Avoid creating "star schemas" where multiple nodes all point to/from a central node.
          Instead, build chains of influence where behaviors and factors lead to each other in meaningful sequences.

          Example of star schema to AVOID:
          Factor1 -> CentralNode
          Factor2 -> CentralNode
          Factor3 -> CentralNode
          Factor4 -> CentralNode

          Example of good chain structure:
          Factor1 -> Factor2 -> Behavior1 -> Behavior2
          Factor3 -> Factor2
          Factor4 -> Behavior1

          Provide the resulting list of relationships in the following JSON format:
          [
            {{
              "source": "source_label",
              "target": "target_label",
            }},
            ...
          ]

          Observable Behaviors:
          {observables_json}

          Contributing Factors:
          {inferrables_json}
        """
    ).strip()


def get_json_formatting_prompt(with_time: bool = False) -> Callable[[str], str]:
    base_schema = {
        "description": "The original statement text verbatim",
        "label": "LABEL_FOR_THE_STATEMENT_IN_SNAKE_CASE",
    }

    schema = (
        base_schema
        | {
            # 99% of conversations are from the same day, so we just assume one date per conversation
            # "date": "YYYY-MM-DD of the related statement",
            "time": "HH:MM:SS of the related statement",
        }
        if with_time
        else base_schema
    )

    return lambda text: dedent(
        f"""
          The following text contains a list, return a JSON object with the following schema for each list item:

          [
            {schema}
          ]

          Here is the text to format:
          {text}
        """
    ).strip()


def parse_graph_nodes(text: str) -> list[dict] | None:
    try:
        res = repair_json(text, return_objects=True)
        if isinstance(res, list) and all(
            "description" in item and "label" in item for item in res
        ):
            return res
        else:
            return None
    except Exception:
        return None


def parse_graph_edges(text: str) -> list[dict] | None:
    try:
        res = repair_json(text, return_objects=True)
        if isinstance(res, list) and all(
            "source" in item and "target" in item for item in res
        ):
            return res
        else:
            return None
    except Exception:
        return None


class ConversationClaimsConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None
    only_personal: bool = Field(
        default=True, description="Only process personal conversations"
    )
    with_causal_relationships: bool = Field(
        default=False, description="Include causal relationships in the output"
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "skeletons_categorized": AssetIn(
            key=["skeletons_categorized"],
        ),
    },
    io_manager_key="parquet_io_manager",
    # op_tags=get_k8s_vllm_config(),
)
async def skeleton_claims(
    context: AssetExecutionContext,
    config: ConversationClaimsConfig,
    llama70b: BaseLlmResource,
    skeletons_categorized: pl.DataFrame,
):
    logger = context.log
    reasoning_llm = llama70b

    df = (
        skeletons_categorized.with_columns(
            pl.col("skeleton")
            .map_elements(
                lambda x: "\n".join(
                    [
                        f"Q at {y['time'].split('.')[0]}: {y['question']}\nA: {y['answer']}"
                        for y in x
                    ]
                )
            )
            .alias("skeleton_text")
        )
        .filter(
            # TODO: We only process personal conversations for now but this should be configurable by the user
            pl.col("is_personal") if config.only_personal else pl.lit(True)
        )
        .slice(0, config.row_limit)
    )

    logger.info(f"Processing {df.height} conversations...")

    logger.info("Extracting observables...")
    (
        formatted_observables_completions,
        formatted_observables_cost,
    ) = reasoning_llm.get_prompt_sequences_completions_batch(
        [
            get_observables_extraction_prompt_sequence(row["skeleton_text"])
            for row in df.to_dicts()
        ]
    )
    logger.info(f"Execution cost: ${formatted_observables_cost:.2f}")

    logger.info("Extracting inferrables...")
    (
        formatted_inferrables_completions,
        formatted_inferrables_cost,
    ) = reasoning_llm.get_prompt_sequences_completions_batch(
        [
            get_inferrables_extraction_prompt_sequence(
                formatted_observables_completion[-2]
            )
            if formatted_observables_completion
            else []
            for formatted_observables_completion in formatted_observables_completions
        ]
    )
    logger.info(f"Execution cost: ${formatted_inferrables_cost:.2f}")

    logger.info("Extracting speculatives...")
    (
        formatted_speculatives_completions,
        formatted_speculatives_cost,
    ) = reasoning_llm.get_prompt_sequences_completions_batch(
        [
            get_speculatives_extraction_prompt_sequence(
                formatted_observables_completion[-1],
                formatted_inferrables_completion[-1],
            )
            if formatted_observables_completion and formatted_inferrables_completion
            else []
            for (
                formatted_observables_completion,
                formatted_inferrables_completion,
            ) in zip(
                formatted_observables_completions, formatted_inferrables_completions
            )
        ]
    )
    logger.info(f"Execution cost: ${formatted_speculatives_cost:.2f}")

    logger.info("Extracting causal relationships...")
    (
        causal_relationships_completions,
        causal_relationships_cost,
    ) = reasoning_llm.get_prompt_sequences_completions_batch(
        [
            [
                get_causal_relationships_extraction_prompt(
                    formatted_observables_completion[-1],
                    formatted_inferrables_completion[-1],
                )
            ]
            if formatted_observables_completion and formatted_inferrables_completion
            else []
            for (
                formatted_observables_completion,
                formatted_inferrables_completion,
            ) in zip(
                formatted_observables_completions, formatted_inferrables_completions
            )
        ]
        if config.with_causal_relationships
        else [[] for _ in range(df.height)]
    )
    logger.info(f"Execution cost: ${causal_relationships_cost:.2f}")

    total_cost = (
        formatted_observables_cost
        + formatted_inferrables_cost
        + formatted_speculatives_cost
        + causal_relationships_cost
    )
    logger.info(f"Total cost: ${total_cost:.2f}")

    results = [
        {
            "inferrables": parse_graph_nodes(formatted_inferrables_completion[-1])
            if formatted_inferrables_completion
            else None,
            "observables": parse_graph_nodes(formatted_observables_completion[-1])
            if formatted_observables_completion
            else None,
            "speculatives": parse_graph_nodes(formatted_speculatives_completion[-1])
            if formatted_speculatives_completion
            else None,
            "causal_relationships": parse_graph_edges(
                causal_relationships_completion[-1]
            )
            if causal_relationships_completion
            else None,
        }
        for (
            formatted_observables_completion,
            formatted_inferrables_completion,
            formatted_speculatives_completion,
            causal_relationships_completion,
        ) in zip(
            formatted_observables_completions,
            formatted_inferrables_completions,
            formatted_speculatives_completions,
            causal_relationships_completions,
        )
    ]

    result = df.hstack(pl.DataFrame(results, strict=False))

    invalid_results = result.filter(
        pl.col("observables").is_null()
        | pl.col("inferrables").is_null()
        | pl.col("speculatives").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # Output:
    # ... | speculatives              | inferrables               | observables               | causal_relationships
    # ----|---------------------------|---------------------------|---------------------------|--------------------------
    # ... | List[{description,label}] | List[{description,label}] | List[{description,label}] | List[{source,target}]
    return result.drop(
        ["causal_relationships"] if not config.with_causal_relationships else []
    )
