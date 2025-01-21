from typing import List, Tuple

import faiss
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import user_partitions_def


class WhatsappClaimsDeduplicatedConfig(Config):
    threshold: float = Field(
        default=0.9, description="Cosine similarity threshold for merging claims"
    )


def find_similar_pairs(
    embeddings: List[List[float]], threshold: float
) -> List[Tuple[int, List[Tuple[int, float]]]]:
    """
    Performs a single FAISS similarity search and returns all similar claim pairs.

    Returns:
        List of tuples (claim_idx, [(similar_claim_idx, similarity_score)])
    """
    if not embeddings:
        return []

    embeddings_array = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings_array)

    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_array)

    similarities, indices = index.search(embeddings_array, k=len(embeddings))

    similar_pairs = []
    for i, (sim_scores, idx_list) in enumerate(zip(similarities, indices)):
        matches = []
        for j, sim in zip(idx_list, sim_scores):
            if i != j and sim >= threshold:
                matches.append((j, float(sim)))
        similar_pairs.append((i, matches))

    return similar_pairs


class UnionFind:
    """
    A simple Disjoint Set / Union-Find data structure to merge
    similar claims into clusters.
    """

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int):
        rootX = self.find(x)
        rootY = self.find(y)
        if rootX != rootY:
            # Union by rank
            if self.rank[rootX] < self.rank[rootY]:
                rootX, rootY = rootY, rootX
            self.parent[rootY] = rootX
            if self.rank[rootX] == self.rank[rootY]:
                self.rank[rootX] += 1


def get_dedup_clusters(
    n: int,
    similar_pairs: List[Tuple[int, List[Tuple[int, float]]]],
) -> list[int]:
    uf = UnionFind(n)
    for i, matches in similar_pairs:
        for j, _sim_score in matches:
            uf.union(i, j)

    return [uf.find(i) for i in range(n)]


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_claims_embeddings": AssetIn(
            key=["whatsapp_claims_embeddings"],
        ),
    },
)
async def whatsapp_claims_deduplicated(
    context: AssetExecutionContext,
    config: WhatsappClaimsDeduplicatedConfig,
    whatsapp_claims_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    """
    Given a Polars DataFrame with columns such as:
        - "embedding": List[float] (the claim embedding)
        - "claim_text": str         (optional actual text)
        - "id": some unique ID      (optional, if you have it)
    this asset will group claims that are similar (based on FAISS)
    and produce a DataFrame of aggregated/deduplicated claims.
    """

    # Gather embeddings and find similarities
    df = whatsapp_claims_embeddings
    embeddings = df["embedding"].to_list()

    similar_pairs = find_similar_pairs(embeddings, config.threshold)
    clusters = get_dedup_clusters(df.height, similar_pairs)

    df = df.with_columns(pl.Series(name="cluster_id", values=clusters))

    # Aggregate clusters:
    # We just keep the first instance of each duplicate
    aggregated = (
        df.group_by("cluster_id", "claim_subject")
        .agg(
            [
                pl.col("cluster_id").count().alias("claim_frequency"),
                pl.col("claim_text").first().alias("claim_text"),
                pl.col("claim_datetime").min().alias("claim_datetime_start_dt"),
                pl.col("claim_datetime").max().alias("claim_datetime_end_dt"),
                pl.col("embedding").first().alias("embedding"),
                # This prioritizes inferrable over speculative
                pl.col("claim_type").sort().first().alias("claim_type"),
            ]
        )
        .drop("cluster_id")
    )

    # Return aggregated (deduplicated) DataFrame
    return aggregated
