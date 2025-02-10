import asyncio
import logging
from typing import Tuple

import networkx as nx
import numpy as np
import polars as pl
import psycopg
from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient
from ai_agents.graph_explorer_agent.actions.get_causal_chain import get_causal_chain
from ai_agents.graph_explorer_agent.actions.get_raw_data import get_raw_data
from ai_agents.graph_explorer_agent.actions.get_relatives import (
    get_children,
    get_parents,
)
from ai_agents.graph_explorer_agent.actions.get_similar_nodes import get_similar_nodes
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from pydantic import BaseModel
from sklearn.decomposition import PCA  # noqa: I001

from query_service.dependencies import (
    PCAReducers,
    get_db,
    get_embedder_client,
    get_graph_df,
    get_pca_reducers,
    get_raw_data_df,
)
from query_service.pad_vectors import pad_vectors
from query_service.pre_init import pre_init


class QueryRequest(BaseModel):
    query: str
    to_embed_nodes: list[str] = []
    to_embed_raw_data: list[str] = []


class CausalChainRequest(BaseModel):
    node_id1: str
    node_id2: str


class NodeRequest(BaseModel):
    node_id: str


pre_init()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# TODO: this is just for dev
similar_nodes_semaphore = asyncio.Semaphore(1)

# Get the logger
logger = logging.getLogger(__name__)


@app.post("/similar_nodes")
async def similar_nodes(
    request: QueryRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
    embedder_client: BaseEmbedderClient = Depends(get_embedder_client),
):
    """Get similar nodes for a query."""
    async with similar_nodes_semaphore:  # This ensures only one request runs at a time
        try:
            G, df = graph_and_df
            label_embeddings = df.select("id", "embedding").to_dicts()
            return await get_similar_nodes(
                G,
                label_embeddings,
                embedder_client,
                request.query,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/causal_chain")
async def causal_chain(
    request: CausalChainRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
):
    """Get causal chain between two nodes."""
    try:
        G, _ = graph_and_df
        return get_causal_chain(G, request.node_id1, request.node_id2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/parents")
async def parents(
    request: NodeRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
):
    """Get parent nodes."""
    try:
        G, _ = graph_and_df
        return get_parents(G, request.node_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/children")
async def children(
    request: NodeRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
):
    """Get child nodes."""
    try:
        G, _ = graph_and_df
        return get_children(G, request.node_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/raw_data")
async def raw_data(
    request: NodeRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
    raw_data_df: pl.DataFrame = Depends(get_raw_data_df),
):
    """Get raw data for a node."""
    try:
        _, nodes_df = graph_and_df
        return get_raw_data(nodes_df, raw_data_df, request.node_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Helper function to get reduced embeddings
async def _get_reduced_embeddings(
    texts: list[str],
    embedder_client: BaseEmbedderClient,
    pca_reducer: PCA,
) -> list[list[float]]:
    _, embeddings = await embedder_client.get_embeddings(texts)
    return pad_vectors(pca_reducer.transform(np.array(embeddings)))


@app.post("/sql_query")
async def sql_query(
    request: QueryRequest,
    db: psycopg.Connection = Depends(get_db),
    embedder_client: BaseEmbedderClient = Depends(get_embedder_client),
    pca_reducers: PCAReducers = Depends(get_pca_reducers),
):
    with db as conn:
        cur = conn.cursor(row_factory=dict_row)
        try:
            # Start transaction explicitly
            cur.execute("BEGIN")
            embeddings = []

            # Add node embeddings to the query
            if request.to_embed_nodes:
                node_embeddings = await _get_reduced_embeddings(
                    request.to_embed_nodes,
                    embedder_client,
                    pca_reducers.nodes_reducer,
                )
                embeddings.extend(node_embeddings)

            # Add raw data embeddings to the query
            if request.to_embed_raw_data:
                raw_data_embeddings = await _get_reduced_embeddings(
                    request.to_embed_raw_data,
                    embedder_client,
                    pca_reducers.raw_data_reducer,
                )
                embeddings.extend(raw_data_embeddings)

            # Add embedding types to the query
            embedding_types = ["nodes"] * len(request.to_embed_nodes) + [
                "rawData"
            ] * len(request.to_embed_raw_data)

            # Insert embeddings into temporary table
            cur.execute(
                """
                CREATE TEMPORARY TABLE QueryEmbedding (
                    id integer,
                    type text,
                    embedding public.vector(2000)
                ) ON COMMIT DROP;
            """
            )

            # Use executemany for bulk insertion
            cur.executemany(
                """
                INSERT INTO QueryEmbedding (id, type, embedding) VALUES (%s, %s, %s)
                """,
                [
                    (i, embedding_types[i], embeddings[i])
                    for i in range(len(embeddings))
                ],
            )

            # Run query
            cur.execute(request.query)
            results = cur.fetchall()

            # Remove embedding columns if they exist
            cleaned_results = [
                {k: v for k, v in row.items() if not k.endswith("embedding")}
                for row in results
            ]

            # Commit the transaction
            cur.execute("COMMIT")
            cur.close()

            return cleaned_results

        except Exception as e:
            if cur and not cur.closed:
                cur.execute("ROLLBACK")
                cur.close()
            logger.error(f"SQL Query Error - Query: {request.query}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
