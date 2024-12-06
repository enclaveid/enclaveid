import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from fast_graphrag import GraphRAG

from data_pipeline.consts import PRODUCTION_STORAGE_BUCKET
from data_pipeline.partitions import user_partitions_def

DOMAIN = """
IMPORTANT: The examples you'll see in this prompt are related to physical entities, but the domain of analysis is more abstract:
In our case we are analyzing a causal sequence of claims about a person: the nodes of the graph are claims about the user, and the edges are causal relationships between claims.
The real data you will be provided with, will contain first a list of claims, and then a text with the causal relationships between them.
"""
ENTITY_TYPES = ["CLAIM (this is the only node type)"]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversation_claims": AssetIn(
            key=["conversation_claims"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def base_graph(
    context: AssetExecutionContext,
    conversation_claims: pl.DataFrame,
) -> None:
    df = conversation_claims

    working_dir = PRODUCTION_STORAGE_BUCKET / "base_graph" / context.partition_key

    # Sample 1 claim for each of 5 sampled conversations
    example_queries = np.array(
        df["speculatives"].list.sample(1).sample(5).to_list()
    ).flatten()

    grag = GraphRAG(
        working_dir=working_dir,
        domain=DOMAIN,
        example_queries="\n".join(example_queries),
        entity_types=ENTITY_TYPES,
    )

    total_rows = len(df)

    for i, row in enumerate(df.iter_rows(named=True), start=1):
        grag.insert(
            f"CLAIMS: {row['observables']}, {row['inferrables']}\n"
            f"CAUSAL RELATIONSHIPS: {row['causal_relationships']}"
        )
        context.log.info(f"Inserted {i} out of {total_rows}")

    grag.save_graphml(output_path=(working_dir / "graph.graphml").as_posix())
