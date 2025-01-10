import random
from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from json_repair import repair_json

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


class SubstantiationEvalConfig(Config):
    row_limit: int = 100


def create_eval_prompt_sequence(query: dict) -> PromptSequence:
    list_1 = "List A:\n" + "\n *".join(
        map(lambda x: x["description"], query["similar_nodes"])
    )
    list_2 = "List B:\n" + "\n *".join(
        map(lambda x: x["description"], query["similar_nodes_baseline"])
    )
    list_3 = "List C:\n" + "\n *".join(
        map(lambda x: x["description"], query["similar_nodes_baseline_no_prep"])
    )

    # Randomly shuffle lists to avoid bias
    lists = [list_1, list_2, list_3]
    random.shuffle(lists)

    return [
        dedent(
            f"""
         If you were to substantiate this speculative claim, which of the following lists would be most appropriate to use?

          Speculative claim: "{query['description']}"

          {lists[0]}

          {lists[1]}

          {lists[2]}

          Provide your analysis and conclude with the list number as follows:
          {{
            "best_list": "A" | "B" | "C",
            "relevant_items_per_list": {{
                "A": number,
                "B": number,
                "C": number
            }}
          }}
          """
        ).strip()
    ]


def parse_eval_response(completion: str):
    try:
        result = repair_json(completion, return_objects=True)
        if (
            result
            and isinstance(result, dict)
            and "best_list" in result
            and "relevant_items_per_list" in result
        ):
            return (result["best_list"], result["relevant_items_per_list"])
        return (None, None)
    except Exception:
        return (None, None)


@asset(
    partitions_def=user_partitions_def,
    ins={
        "speculatives_substantiation": AssetIn(
            key=["speculatives_substantiation"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def substantiation_eval(
    context: AssetExecutionContext,
    speculatives_substantiation: pl.DataFrame,
    gemini_pro: BaseLlmResource,
    config: SubstantiationEvalConfig,
) -> pl.DataFrame:
    llm = gemini_pro
    # Filter for successful queries only
    successful_queries = speculatives_substantiation.filter(pl.col("success")).sample(
        n=config.row_limit
    )

    total_queries = successful_queries.height

    context.log.info(f"Evaluating {total_queries} successful substantiations...")

    prompt_sequences = []
    for query in successful_queries.iter_rows(named=True):
        if not query.get("similar_nodes_baseline"):
            continue
        prompt_sequences.append(create_eval_prompt_sequence(query))

    context.log.info(f"Evaluating {len(prompt_sequences)} prompt sequences...")

    # Get completions in batch
    completions, cost = llm.get_prompt_sequences_completions_batch(prompt_sequences)
    context.log.info(f"Evaluation cost: {cost}")

    winners, relevant_items_per_list, analyses = zip(
        *[
            (*parse_eval_response(completion[-1]), completion[-1])
            if completion
            else (None, None, None)
            for completion in completions
        ]
    )

    result_df = successful_queries.with_columns(
        winner=pl.Series(winners, dtype=pl.Utf8),
        analysis=pl.Series(analyses, dtype=pl.Utf8),
        relevant_items_per_list=pl.Series(relevant_items_per_list, dtype=pl.Struct),
        similar_nodes=pl.col("similar_nodes").map_elements(
            lambda x: [node["description"] for node in x]
        ),
        similar_nodes_baseline=pl.col("similar_nodes_baseline").map_elements(
            lambda x: [node["description"] for node in x]
        ),
        similar_nodes_baseline_no_prep=pl.col(
            "similar_nodes_baseline_no_prep"
        ).map_elements(lambda x: [node["description"] for node in x]),
    )

    # Log summary statistics
    if len(result_df) > 0:
        list1_wins = result_df.filter(pl.col("winner") == "A").height
        list2_wins = result_df.filter(pl.col("winner") == "B").height
        list3_wins = result_df.filter(pl.col("winner") == "C").height

        context.log.info(
            dedent(
                f"""
                  Evaluation complete:
                  Total evaluations: {len(result_df)}
                  Graph wins: {list1_wins} ({list1_wins/len(result_df):.1%})
                  Baseline wins: {list2_wins} ({list2_wins/len(result_df):.1%})
                  Speculative baseline wins: {list3_wins} ({list3_wins/len(result_df):.1%})
                """
            ).strip()
        )

    return result_df
