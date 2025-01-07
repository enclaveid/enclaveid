import json
import time
from textwrap import dedent

import faiss
import networkx as nx
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json
from pydantic import Field
from upath import UPath

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.expressions.relevance_period_expr import relevance_period_expr


def get_causality_prompt_sequence(
    current_node: dict, candidate_nodes: list[dict]
) -> list[str]:
    return [
        dedent(
            f"""
            Analyze the following nodes and determine which ones could be interpreted as direct causes of the target node.
            Return a JSON array of labels for nodes that appear to have a causal relationship with the target.

            Target node (occurred later in time):
            Label: {current_node['label']}
            Description: {current_node['description']}
            Relevance period: {current_node['relevance_period']}

            Potential cause nodes (occurred earlier):
            {json.dumps(candidate_nodes, indent=2)}

            Explain your reasoning and, at the end, return a list of labels that are likely to be causes:
            ["label1", "label2", ...]
            """
        ).strip()
    ]


def parse_causal_labels(completion: str) -> list[str] | None:
    try:
        result = repair_json(completion, return_objects=True)
        if result and isinstance(result, list):
            # Ensure list is flat and contains only strings
            if all(isinstance(item, str) for item in result):
                return result
            return None
        return None
    except Exception:
        return None


class RecursiveCausalityConfig(RowLimitConfig):
    row_limit: int | None = None

    top_k: int = Field(
        default=20, description="The number of similar nodes to consider for each node"
    )

    similarity_threshold: float = Field(
        default=0.7,
        description="The similarity threshold for considering a node as a cause",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph_w_embeddings": AssetIn(
            key=["deduplicated_graph_w_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def recursive_causality(
    context: AssetExecutionContext,
    llama70b: BaseLlmResource,
    deduplicated_graph_w_embeddings: pl.DataFrame,
    config: RecursiveCausalityConfig,
) -> pl.DataFrame:
    logger = context.log
    llm = llama70b

    # Filter and sort nodes
    nodes_df = (
        deduplicated_graph_w_embeddings.filter(
            pl.col("node_type").is_in(["inferrable", "observable"])
        )
        .sort(["end_date", "end_time"], descending=False)
        .with_columns(relevance_period=relevance_period_expr)
        .slice(0, config.row_limit)
    )

    # Initialize FAISS index with cosine similarity
    embedding_dim = len(nodes_df.get_column("embedding")[0])
    index = faiss.IndexFlatIP(embedding_dim)  # inner-product index

    # Initialize NetworkX graph
    G = nx.DiGraph()

    # We'll store debug rows and total cost
    debug_rows = []
    total_cost = 0.0

    # ---------------------
    # 1) Collect prompts
    # ---------------------
    # We'll store all prompt sequences here, then call the LLM once.
    prompt_sequences = []
    # This will store (node_idx, prompt_index_in_list)
    # so we can map completions back to the correct node.
    prompt_metadata = []

    # TODO: We could batch this but we need to handle chronological incrementality
    logger.info(f"Computing candidates for {len(nodes_df)} nodes")
    t0 = time.time()
    for i, row in enumerate(nodes_df.iter_rows(named=True)):
        # Prepare debug info for the current node
        debug_info = {
            "label": row["label"],
            "candidate_nodes": [],
            "causal_labels": [],
            "raw_causal_analysis": "",
        }

        current_embedding = np.array([row["embedding"]], dtype=np.float32)

        # Skip first node as it can't have causes
        if i > 0:
            # Search similar nodes that came before
            D, I = index.search(current_embedding, min(config.top_k, i))

            # Filter indices by similarity threshold
            similar_candidates = [
                (I[0][j], D[0][j])
                for j in range(len(I[0]))
                if D[0][j] > config.similarity_threshold
            ]

            # If fewer than top_k, add temporal candidates
            if len(similar_candidates) < config.top_k:
                # Add nodes that occurred just before
                needed = config.top_k - len(similar_candidates)
                temporal_candidates = range(max(0, i - needed), i)
                existing_indices = {idx for idx, _ in similar_candidates}
                for idx_temporal in temporal_candidates:
                    if idx_temporal not in existing_indices:
                        similar_candidates.append((idx_temporal, 0.0))

            # Build candidate list for LLM
            candidate_nodes = []
            for idx_sim, sim_val in similar_candidates:
                node_info = nodes_df.row(idx_sim, named=True)
                candidate_nodes.append(
                    {
                        "label": node_info["label"],
                        "description": node_info["description"],
                        "relevance_period": node_info["relevance_period"],
                        "similarity": float(sim_val),
                    }
                )

            debug_info["candidate_nodes"] = candidate_nodes

            # Build prompt for the LLM
            current_node = {
                "label": row["label"],
                "description": row["description"],
                "relevance_period": row["relevance_period"],
            }
            prompt_sequence = get_causality_prompt_sequence(
                current_node, candidate_nodes
            )

            # Instead of calling the LLM here, store the prompt and metadata
            prompt_index = len(prompt_sequences)  # index of the new prompt
            prompt_sequences.append(prompt_sequence)
            prompt_metadata.append((i, prompt_index))

        # Add current node embedding to index (for the next nodes)
        index.add(current_embedding)

        # Add node to graph
        G.add_node(
            row["label"],
            description=row["description"] or "",
            category=row["category"] or "",
            node_type=row["node_type"] or "",
            relevance_period=row["relevance_period"] or "",
        )

        # Add an entry for each row to debug_rows
        # (We'll fill in "causal_labels" later after we parse completions)
        debug_rows.append(debug_info)

    logger.info(
        f"Computed candidates for {len(nodes_df)} nodes in {time.time() - t0:.2f} seconds"
    )

    # ---------------------
    # 2) Batch LLM call
    # ---------------------
    if prompt_sequences:
        # Get all completions in one (big) batch
        completions_list, cost = llm.get_prompt_sequences_completions_batch(
            prompt_sequences
        )
        total_cost += cost

        # ---------------------
        # 3) Parse all completions
        # ---------------------
        # completions_list is a list of lists (each prompt may have multiple completions)
        # We'll assume we only care about completions_list[i][-1] (the last completion for prompt i).
        for node_index, prompt_idx in prompt_metadata:
            completion_text = (
                completions_list[prompt_idx][-1] if completions_list[prompt_idx] else ""
            )
            debug_rows[node_index]["raw_causal_analysis"] = completion_text

            causal_labels = parse_causal_labels(completion_text)
            if causal_labels:
                debug_rows[node_index]["causal_labels"] = causal_labels
                # Add edges to graph
                current_label = debug_rows[node_index]["label"]
                for cause_label in causal_labels:
                    G.add_edge(cause_label, current_label)

    logger.info(f"Total LLM cost: ${total_cost:.4f}")
    logger.info(
        f"Final graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
    )

    # Write graph & debug data to disk
    working_dir = DAGSTER_STORAGE_DIRECTORY / UPath(context.asset_key.path[-1])
    working_dir.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, f"{working_dir}/{context.partition_key}.graphml")

    return (
        deduplicated_graph_w_embeddings.join(
            pl.DataFrame(debug_rows), on="label", how="left"
        )
        .drop(["edges"])
        .rename({"causal_labels": "edges"})
    )
