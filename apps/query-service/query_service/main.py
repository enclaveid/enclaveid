from .pre_init import pre_init  # noqa: I001

from typing import Tuple
import logging

import networkx as nx
import polars as pl
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
from pydantic import BaseModel
import asyncio

from .dependencies import get_embedder_client, get_graph_df, get_raw_data_df


class QueryRequest(BaseModel):
    query: str


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


@app.post("/sql_query")
async def sql_query(
    request: QueryRequest,
    graph_and_df: Tuple[nx.DiGraph, pl.DataFrame] = Depends(get_graph_df),
    raw_data_df: pl.DataFrame = Depends(get_raw_data_df),
):
    """Execute a query on the database using plain SQL (ANSI/ISO standard)."""
    try:
        _, nodes_df = graph_and_df
        return (
            pl.SQLContext(frames={"nodes_df": nodes_df, "raw_data_df": raw_data_df})
            .execute(request.query, eager=True)
            .unique()
            .to_dicts()
        )
    except Exception as e:
        logger.error(f"SQL Query Error - Query: {request.query}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
