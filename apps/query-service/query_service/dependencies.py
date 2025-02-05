from functools import lru_cache
from typing import Tuple

import networkx as nx
import polars as pl
from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient
from ai_agents.embeddings.local_embedder_client import LocalEmbedderClient

# TODO: get this from auth
CONST_NODES_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_nodes_deduplicated/00393494197577/0034689896443.snappy"
CONST_SUBGRAPHS_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_chunks_subgraphs/00393494197577/0034689896443.snappy"

MAX_USERS_CACHE_SIZE = 10  # Cache 10 users (once auth implemented)


@lru_cache(maxsize=MAX_USERS_CACHE_SIZE)
def get_graph_df() -> Tuple[nx.DiGraph, pl.DataFrame]:
    df = pl.read_parquet(CONST_NODES_PATH)
    G = nx.DiGraph()
    for row in df.iter_rows(named=True):
        G.add_node(
            row["id"],
            description=row["proposition"],
            frequency=row["frequency"],
            user=row["user"],
            datetime=row["datetimes"],
            chunk_ids=row["chunk_ids"],
        )
        G.add_edges_from([(row["id"], e) for e in row["edges"]])
    return G, df


@lru_cache(maxsize=MAX_USERS_CACHE_SIZE)
def get_raw_data_df() -> pl.DataFrame:
    return pl.read_parquet(CONST_SUBGRAPHS_PATH)


@lru_cache(maxsize=1)
def get_embedder_client() -> BaseEmbedderClient:
    return LocalEmbedderClient()
