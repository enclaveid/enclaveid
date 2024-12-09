from textwrap import dedent

import networkx as nx
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.consts import PRODUCTION_STORAGE_BUCKET, get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.get_logger import get_logger


def get_observables_extraction_prompt(text: str) -> str:
    return dedent(
        f"""
          Given this Q&A conversation between a person and an AI, extract a list of contextually complete facts about the user. Limit your response to facts that are directly evident in their behavior and require no inference beyond the evidence:
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
    ).strip()


# TODO refine
def get_inferrables_extraction_prompt(text: str) -> str:
    return dedent(
        f"""
          Given the following list of behavioral claims about a user for a topical sequence of actions, what reasonable causes for those actions can you infer?

          {text}
        """
    ).strip()


# TODO refine
def get_causal_relationships_extraction_prompt(
    observables_json: str, inferrables_json: str
) -> str:
    return dedent(
        f"""
          Given a list of actions and potential causes for those actions, generate the list of relevant causal relationships.
          The causal relationships can also be cause <-> cause and action <-> action if relevant.

          Provide your answer in JSON format:
          [
            {{
              "source": "label_1",
              "target": "label_2"
            }},
            ...
          ]

          Actions:
          {observables_json}

          Causes:
          {inferrables_json}
        """
    ).strip()


def get_json_formatting_prompt(text: str) -> str:
    return dedent(
        f"""
          Given a list of statements, return a JSON object with the following schema:

          [
            {{
              "description": "The original statement text verbatim",
              "label": "THE_LABEL_OF_THE_STATEMENT"
            }}
          ]
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
    row_limit = 500 if get_environment() == "LOCAL" else None

    save_subgraphs: bool = Field(
        default=False,
        description=("Save subgraphs to disk in .graphml format for debugging."),
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversation_skeletons": AssetIn(
            key=["conversation_skeletons"],
        ),
    },
    io_manager_key="parquet_io_manager",
    # op_tags=get_k8s_vllm_config(),
)
async def conversation_claims(
    context: AssetExecutionContext,
    config: ConversationClaimsConfig,
    llama70b: BaseLlmResource,
    llama8b: BaseLlmResource,
    conversation_skeletons: pl.DataFrame,
):
    logger = get_logger(context)

    df = (conversation_skeletons).slice(0, config.row_limit)

    logger.info(f"Processing {df.height} conversations...")

    logger.info("Extracting observables...")
    (
        raw_observables_completions,
        raw_observables_cost,
    ) = llama70b.get_prompt_sequences_completions_batch(
        [get_observables_extraction_prompt(row["skeleton"]) for row in df.to_dicts()]
    )
    logger.info(f"Execution cost: ${raw_observables_cost:.2f}")

    logger.info("Formatting raw observables...")
    (
        formatted_observables_completions,
        formatted_observables_cost,
    ) = llama8b.get_prompt_sequences_completions_batch(
        [
            get_json_formatting_prompt(raw_observables_completion[-1])
            for raw_observables_completion in raw_observables_completions
        ]
    )
    logger.info(f"Execution cost: ${formatted_observables_cost:.2f}")

    logger.info("Extracting inferrables...")
    (
        raw_inferrables_completions,
        raw_inferrables_cost,
    ) = llama70b.get_prompt_sequences_completions_batch(
        [
            get_inferrables_extraction_prompt(raw_observables_completion[-1])
            for raw_observables_completion in raw_observables_completions
        ]
    )
    logger.info(f"Execution cost: ${raw_inferrables_cost:.2f}")

    logger.info("Formatting raw inferrables...")
    (
        formatted_inferrables_completions,
        formatted_inferrables_cost,
    ) = llama8b.get_prompt_sequences_completions_batch(
        [
            get_json_formatting_prompt(raw_inferrables_completion[-1])
            for raw_inferrables_completion in raw_inferrables_completions
        ]
    )
    logger.info(f"Execution cost: ${formatted_inferrables_cost:.2f}")

    logger.info("Extracting causal relationships...")
    (
        causal_relationships_completions,
        causal_relationships_cost,
    ) = llama70b.get_prompt_sequences_completions_batch(
        [
            get_causal_relationships_extraction_prompt(
                formatted_observables_completion[-1],
                formatted_inferrables_completion[-1],
            )
            for (
                formatted_observables_completion,
                formatted_inferrables_completion,
            ) in zip(
                formatted_observables_completions, formatted_inferrables_completions
            )
        ]
    )
    logger.info(f"Execution cost: ${causal_relationships_cost:.2f}")

    total_cost = (
        raw_observables_cost
        + formatted_observables_cost
        + raw_inferrables_cost
        + formatted_inferrables_cost
        + causal_relationships_cost
    )
    logger.info(f"Total cost: ${total_cost:.2f}")

    results = [
        {
            "inferrables": parse_graph_nodes(formatted_inferrables_completion[-1]),
            "observables": parse_graph_nodes(formatted_observables_completion[-1]),
            "causal_relationships": parse_graph_edges(
                causal_relationships_completion[-1]
            ),
        }
        if (
            formatted_observables_completion
            and formatted_inferrables_completion
            and causal_relationships_completion
        )
        else {
            "inferrables": None,
            "observables": None,
            "causal_relationships": None,
        }
        for (
            formatted_observables_completion,
            formatted_inferrables_completion,
            causal_relationships_completion,
        ) in zip(
            formatted_observables_completions,
            formatted_inferrables_completions,
            causal_relationships_completions,
        )
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(
        pl.col("causal_relationships").is_null()
        | pl.col("observables").is_null()
        | pl.col("inferrables").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    filtered_result = result.filter(pl.col("datetime_conversations").is_not_null())

    working_dir = PRODUCTION_STORAGE_BUCKET / "conversation_claims"
    if config.save_subgraphs:
        working_dir.mkdir(parents=True, exist_ok=True)
        G = nx.DiGraph()
        G.add_nodes_from(filtered_result["inferrables"].to_list())
        G.add_nodes_from(filtered_result["observables"].to_list())
        G.add_edges_from(filtered_result["causal_relationships"].to_list())
        nx.write_graphml(G, working_dir / f"{context.partition_key}.graphml")

    # Output:
    # ... | inferrables               | observables               | causal_relationships
    # ----|---------------------------|---------------------------|-----------------------
    # ... | List[{description,label}] | List[{description,label}] | List[{source,target}]
    return filtered_result
