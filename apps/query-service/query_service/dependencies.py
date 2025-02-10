import os
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

import joblib
import networkx as nx
import polars as pl
import psycopg
from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient
from ai_agents.embeddings.deepinfra_embedder_client import DeepInfraEmbedderClient
from attr import dataclass
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool
from sklearn.decomposition import PCA

# TODO: get this from auth
CONST_NODES_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_nodes_deduplicated/00393494197577/0034689896443.snappy"
CONST_SUBGRAPHS_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_chunks_subgraphs/00393494197577/0034689896443.snappy"

MAX_USERS_CACHE_SIZE = 10  # Cache 10 users (once auth implemented)


@lru_cache(maxsize=MAX_USERS_CACHE_SIZE)
def get_graph_df() -> tuple[nx.DiGraph, pl.DataFrame]:
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
    return DeepInfraEmbedderClient(api_key=os.environ["DEEPINFRA_API_KEY"])


# The pool is shared across requests
@lru_cache(maxsize=1)
def _get_db_pool() -> ConnectionPool:
    print(os.environ["DATABASE_URL"])
    return ConnectionPool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=10,  # TODO
        configure=lambda conn: register_vector(conn),
    )


# Each request gets a new connection from the pool
@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    pool = _get_db_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@dataclass
class PCAReducers:
    nodes_reducer: PCA
    raw_data_reducer: PCA


# TODO
NODES_REDUCER_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_out_nodes/00393494197577/0034689896443.reducer.joblib"
RAW_DATA_REDUCER_PATH = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_out_chunks/00393494197577/0034689896443.reducer.joblib"


@lru_cache(maxsize=1)
def get_pca_reducers() -> PCAReducers:
    return PCAReducers(
        nodes_reducer=joblib.load(NODES_REDUCER_PATH),
        raw_data_reducer=joblib.load(RAW_DATA_REDUCER_PATH),
    )
