from textwrap import dedent
from time import time

import faiss
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from json_repair import repair_json
from pydantic import Field

from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)


class WhatsappSpeculativesSubstantiationConfig(Config):
    top_k: int = Field(
        default=20,
        description="Number of similar nodes to consider for order of substantiation",
    )
    min_score: float | None = Field(
        default=0.6,
        description="Minimum similarity score to consider for order of substantiation",
    )
    min_confidence: float = Field(
        default=0.6,
        description="Minimum confidence score to consider for substantiation",
    )


def create_faiss_index(df: pl.DataFrame) -> faiss.IndexFlatIP:
    """
    Create and populate a FAISS index from embeddings in the given dataframe.
    Assumes df has column 'embedding' containing lists of floats.
    """
    embeddings = np.stack(df.get_column("embedding").to_list())
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))  # type: ignore
    return index


def get_similar_claims(
    idx_to_id: dict[int, int],
    similarities: dict[int, float],
    top_k: int,
    min_score: float | None = None,
):
    """
    Sort nodes by similarity scores (descending) and return the top_k,
    skipping the first item (often the query itself).
    """
    # Filter out nodes below the min_score
    if min_score is not None:
        similarities = {
            idx: score for idx, score in similarities.items() if score >= min_score
        }

    # Sort node indices by descending similarity
    top_node_indices = sorted(
        similarities.keys(),
        key=lambda idx: similarities[idx],
        reverse=True,
    )[1 : top_k + 1]  # skip the first result as it’s usually the query itself

    results = []
    for idx in top_node_indices:
        results.append(
            {
                "id": idx_to_id[idx],
                "score": float(similarities[idx]),
            }
        )
    return results


def get_substantiation_prompt_sequence(
    target_claim_text: str, evidence: list[str]
) -> list[str]:
    return [
        dedent(
            f"""
            Given the following speculative claim: "{target_claim_text}",
            determine if the following evidence supports it:
            {"".join(f"- {ev}\n" for ev in evidence)}

            Provide an analysis of the evidence and conclude with the following JSON:
            {{
                "supports": true | false,
                "confidence": 0-1
            }}
            """
        ).strip()
    ]


def parse_substantiation(response: str) -> tuple[bool | None, float | None]:
    """
    Attempt to parse the GPT response into (supports, confidence).
    Expects a valid JSON with "supports" and "confidence" fields.
    """
    try:
        repaired = repair_json(response, return_objects=True)
        if (
            repaired
            and isinstance(repaired, dict)
            and "supports" in repaired
            and "confidence" in repaired
        ):
            return (repaired["supports"], repaired["confidence"])
        return (None, None)
    except Exception:
        return (None, None)


@asset(
    partitions_def=partitions,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_nodes_deduplicated": AssetIn(
            key=["whatsapp_nodes_deduplicated"],
        ),
    },
)
def whatsapp_speculatives_substantiated(
    context: AssetExecutionContext,
    config: WhatsappSpeculativesSubstantiationConfig,
    whatsapp_nodes_deduplicated: pl.DataFrame,
    gpt4o: BaseLlmResource,
) -> pl.DataFrame:
    """
    Identify speculative claims from whatsapp_nodes_deduplicated, gather
    similar evidence from non-speculative claims, and determine if they are supported.
    """

    # 1) Create an ephemeral ID column for *every* row
    df = whatsapp_nodes_deduplicated.with_row_count("id")

    # 2) Separate query (speculative) vs. non-speculative
    query_claims = df.filter(pl.col("claim_type") == "speculative")
    substantiative_claims = df.filter(pl.col("claim_type") != "speculative")

    # 3) Build the FAISS index from the embeddings in substantiative_claims
    index = create_faiss_index(substantiative_claims)
    # Keep a list of the 'id' values for substantiative_claims in the order they appear
    indexed_ids = substantiative_claims.get_column("id").to_list()

    # 4) Build initial 'similar_claims' mapping: { query_node_id: [ {id, score}, ... ] }
    similar_claims_map = {}
    for row in query_claims.iter_rows(named=True):
        row_id = row["id"]
        if "embedding" not in row or row_id in similar_claims_map:
            continue

        emb = np.array([row["embedding"]], dtype=np.float32)
        D, I = index.search(emb, len(substantiative_claims))

        # create mapping from FAISS index → actual row_id
        idx_to_id = {idx: indexed_ids[idx] for idx in I[0]}

        # top-k neighbors with min_score
        similar_claims_map[row_id] = get_similar_claims(
            idx_to_id, dict(zip(I[0], D[0])), config.top_k, config.min_score
        )

    # 5) Turn that dictionary into a Polars DataFrame
    #    containing columns: id, similar_claims_scored, average_score, similar_ids
    similar_claims_init_df = (
        pl.DataFrame(
            {
                "id": list(similar_claims_map.keys()),
                "similar_claims_scored": list(similar_claims_map.values()),
            }
        )
        .with_columns(
            pl.col("similar_claims_scored")
            .map_elements(lambda arr: [item["score"] for item in arr])
            .list.mean()
            .alias("average_score"),
            pl.col("similar_claims_scored")
            .map_elements(lambda arr: [item["id"] for item in arr])
            .alias("similar_ids"),
        )
        .sort("average_score", descending=True)
    )

    # Join so that each row has original columns + average_score + similar_ids
    similar_claims_init_df = query_claims.join(
        similar_claims_init_df, on="id", how="left"
    )

    # 6) Substantiate each speculative in order of average_score
    start_time = time()
    last_log_time = start_time
    total_labels = len(similar_claims_init_df)
    total_processed = 0
    total_cost = 0.0  # track if your LLM resource gives cost

    context.log.info(f"Processing {total_labels} speculative claims...")

    results = []
    for row in similar_claims_init_df.iter_rows(named=True):
        row_id = row["id"]
        claim_text = row["claim_text"]

        # Re-run search in case we added new embeddings
        emb = np.array([row["embedding"]], dtype=np.float32)
        D, I = index.search(emb, len(substantiative_claims))

        idx_to_id = {idx: indexed_ids[idx] for idx in I[0]}
        top_k_info = get_similar_claims(
            idx_to_id, dict(zip(I[0], D[0])), config.top_k, config.min_score
        )
        top_k_ids = [x["id"] for x in top_k_info]

        # Collect the claim_text from these top_k neighbors
        evidence_texts = (
            df.filter(pl.col("id").is_in(top_k_ids)).get_column("claim_text").to_list()
        )

        if not evidence_texts:
            results.append(
                {
                    "id": row_id,
                    "supports": False,
                    "confidence": 0.0,
                    "substantiation_analysis": "No supporting evidence found",
                    "evidence": [],
                }
            )
            continue

        # If using an actual LLM resource:
        completions, cost = gpt4o.get_prompt_sequences_completions_batch(
            [get_substantiation_prompt_sequence(claim_text, evidence_texts)],
        )
        total_cost += cost

        if not completions:
            continue

        # parse the GPT response
        supports, confidence, substantiation_analysis = zip(
            *[
                (
                    *parse_substantiation(completion[-1]),
                    completion[-1],
                )
                if completion
                else (None, None, None)
                for completion in completions
            ]
        )

        # If the new claim is supported with high confidence, add it to the index
        if (
            supports[0]
            and confidence[0] is not None
            and confidence[0] > config.min_confidence
        ):
            index.add(emb)
            indexed_ids.append(row_id)

        results.append(
            {
                "id": row_id,
                "supports": supports[0],
                "confidence": confidence[0],
                "substantiation_analysis": substantiation_analysis[0],
                "evidence": evidence_texts,
            }
        )

        total_processed += 1
        current_time = time()
        if current_time - last_log_time >= 30:  # log progress every 30s
            elapsed_time = current_time - start_time
            progress = total_processed / total_labels
            est_total_time = elapsed_time / progress if progress > 0 else 0
            remaining_time = est_total_time - elapsed_time
            context.log.info(
                f"{total_processed}/{total_labels} claims ({progress:.1%}) | "
                f"Est. remaining: {remaining_time/60:.1f}min | "
                f"Total cost: ${total_cost:.2f}"
            )
            last_log_time = current_time

    # Final stats logging
    total_time = (time() - start_time) / 60
    context.log.info(
        f"Completed processing {total_labels} speculative claims. "
        f"Total time: {total_time:.1f}min, Total cost: ${total_cost:.2f}"
    )

    # 7) Attach our result columns (supports, confidence, etc.) back to the original DF
    results_df = pl.DataFrame(results)
    enriched_df = df.join(results_df, on="id", how="left")

    return enriched_df
