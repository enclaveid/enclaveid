from textwrap import dedent
from time import time

import faiss
import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    asset,
)
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


class SpeculativesSubstantiationConfig(Config):
    row_limit: int | None = None if get_environment() == "LOCAL" else None
    top_k: int = Field(
        default=20,
        description="Number of similar nodes to consider for order of substantiation",
    )
    min_score: float | None = Field(
        default=0.7,
        description="Minimum similarity score to consider for order of substantiation",
    )
    min_confidence: float = Field(
        default=0.6,
        description="Minimum confidence score to consider for substantiation",
    )


def create_faiss_index(graph_nodes: pl.DataFrame) -> faiss.IndexFlatIP:
    """Create and populate FAISS index from graph node embeddings."""
    embeddings = np.stack(graph_nodes.get_column("embedding").to_list())
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))  # type: ignore
    return index


def get_similar_nodes(
    idx_to_label: dict[int, str],
    similarities: dict[int, float],
    top_k: int,
    min_score: float | None = None,
):
    """
    Get baseline RAG results by sorting nodes according to `similarities` (i.e., top_k).
    Skips the first node as it's typically a self-match.
    """
    # Filter out nodes with similarity score below min_score
    if min_score:
        similarities = {
            idx: score for idx, score in similarities.items() if score >= min_score
        }
    # Sort node indices by max similarity
    top_node_indices = sorted(
        similarities.keys(),
        key=lambda idx: similarities[idx],
        reverse=True,
    )[1 : top_k + 1]  # Skip first result and take next top_k

    results = []
    for idx in top_node_indices:
        results.append(
            {
                "label": idx_to_label[idx],
                "score": float(similarities[idx]),
            }
        )

    return results


def get_substantiation_prompt_sequence(
    target_description: str, evidence: list[str]
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given the following speculative claim about a user: "{target_description}", determine if the following evidence supports it:
            {"\n".join(f"- {desc}" for desc in evidence)}

            Answer with the following JSON:
            {{
                "supports": true | false,
                "confidence": 0-1
            }}
            """
        ).strip()
    ]


def parse_substantiation(response: str) -> tuple[bool | None, float | None]:
    try:
        result = repair_json(response, return_objects=True)
        if (
            result
            and isinstance(result, dict)
            and "supports" in result
            and "confidence" in result
        ):
            return (result["supports"], result["confidence"])
        return (None, None)
    except Exception:
        return (None, None)


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph_w_embeddings": AssetIn(
            key=["deduplicated_graph_w_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def speculatives_substantiation(
    context: AssetExecutionContext,
    deduplicated_graph_w_embeddings: pl.DataFrame,
    config: SpeculativesSubstantiationConfig,
    gpt4o: BaseLlmResource,
) -> pl.DataFrame:
    llm = gpt4o

    query_nodes = deduplicated_graph_w_embeddings.filter(
        pl.col("node_type") == "speculative"
    ).slice(0, config.row_limit)

    graph_nodes = deduplicated_graph_w_embeddings.filter(
        pl.col("node_type") != "speculative"
    )

    # Create FAISS index from all the graph nodes
    index = create_faiss_index(graph_nodes)
    # Keep track of all nodes in the index and their positions
    indexed_nodes = graph_nodes.get_column("label").to_list()

    similar_nodes = {}
    # Go through each speculative node
    for row in query_nodes.iter_rows(named=True):
        lbl = row["label"]
        # If there's no embedding or we already processed it, skip
        if "embedding" not in row or lbl in similar_nodes:
            continue

        # Search in FAISS
        D, I = index.search(
            np.array([row["embedding"]], dtype=np.float32), len(graph_nodes)
        )

        idx_to_label = {idx: indexed_nodes[idx] for idx in I[0]}

        # Build the baseline top-k
        similar_nodes[lbl] = get_similar_nodes(
            idx_to_label, dict(zip(I[0], D[0])), config.top_k, config.min_score
        )

    # Create a dataframe of label, similar_nodes
    similar_nodes_init_df = (
        pl.DataFrame(
            {
                "label": [lbl for lbl in similar_nodes],
                "similar_labels_scored": [similar_nodes[lbl] for lbl in similar_nodes],
            }
        )
        .with_columns(
            pl.col("similar_labels_scored")
            .map_elements(lambda x: [item["score"] for item in x])
            .list.mean()
            .alias("average_score"),
            pl.col("similar_labels_scored")
            .map_elements(lambda x: [item["label"] for item in x])
            .alias("similar_labels"),
        )
        .sort("average_score", descending=True)
    )

    similar_nodes_init_df = query_nodes.join(
        similar_nodes_init_df, on="label", how="left"
    )

    # Add timing variables before the result loop
    start_time = time()
    last_log_time = start_time
    total_labels = len(similar_nodes_init_df)
    total_processed = 0

    context.log.info(f"Processing {total_labels} speculative nodes...")

    # Substantiate each speculative in order of likelihood and add back to the index
    result = []
    total_cost = 0
    for row in similar_nodes_init_df.iter_rows(named=True):
        lbl = row["label"]
        description = row["description"]
        similar_labels = row["similar_labels"]

        # Search in FAISS, including newly substantiated nodes
        emb = np.array([row["embedding"]], dtype=np.float32)
        D, I = index.search(emb, len(graph_nodes))

        idx_to_label = {idx: indexed_nodes[idx] for idx in I[0]}

        similar_labels = [
            node["label"]
            for node in get_similar_nodes(
                idx_to_label, dict(zip(I[0], D[0])), config.top_k
            )
        ]

        evidence = (
            deduplicated_graph_w_embeddings.filter(
                pl.col("label").is_in(similar_labels)
            )
            .get_column("description")
            .to_list()
        )

        completions, cost = llm.get_prompt_sequences_completions_batch(
            [get_substantiation_prompt_sequence(description, evidence)],
        )
        total_cost += cost

        if not completions:
            continue

        supports, confidence, substantiation_analysis = zip(
            *[
                (*parse_substantiation(completion[-1]), completion[-1])
                if completion
                else (None, None, None)
                for completion in completions
            ]
        )

        # Add back to the index if the claim is supported
        if supports[0] and confidence[0] > config.min_confidence:
            index.add(emb)
            indexed_nodes.append(lbl)  # Keep track of the new node's label

        result.append(
            {
                "label": lbl,
                "supports": supports[0],
                "confidence": confidence[0],
                "substantiation_analysis": substantiation_analysis[0],
            }
        )

        # Add progress logging
        total_processed += 1
        current_time = time()
        if current_time - last_log_time >= 30:  # Log every 30 seconds
            elapsed_time = current_time - start_time
            progress = total_processed / total_labels
            estimated_total_time = elapsed_time / progress if progress > 0 else 0
            remaining_time = estimated_total_time - elapsed_time

            context.log.info(
                f"{total_processed}/{total_labels} nodes ({progress:.1%}) | "
                f"Est. remaining time: {remaining_time/60:.1f}min | "
                f"Total cost: ${total_cost:.2f}"
            )
            last_log_time = current_time

    # Add final stats logging
    total_time = (time() - start_time) / 60
    context.log.info(
        f"Completed processing {total_labels} nodes | "
        f"Total time: {total_time:.1f}min | "
        f"Total cost: ${total_cost:.2f}"
    )

    return deduplicated_graph_w_embeddings.join(
        pl.DataFrame(result), on="label", how="left"
    )
