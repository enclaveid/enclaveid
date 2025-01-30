import networkx as nx
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource
from data_pipeline.resources.graph_explorer_agent.resource import (
    GraphExplorerAgentResource,
)
from data_pipeline.resources.graph_explorer_agent.types import ActionsImpl
from data_pipeline.utils.agent_actions import (
    get_causal_chain,
    get_children,
    get_similar_nodes,
)
from data_pipeline.utils.agent_actions.get_relatives import (
    get_parents,
)
from data_pipeline.utils.get_node_datetime import get_node_datetime


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_nodes_deduplicated": AssetIn(
            key=["whatsapp_nodes_deduplicated"],
        ),
    },
)
def whatsapp_hypotheses_validation(
    context: AssetExecutionContext,
    whatsapp_nodes_deduplicated: pl.DataFrame,
    graph_explorer_agent: GraphExplorerAgentResource,
    batch_embedder: BatchEmbedderResource,
):
    df = whatsapp_nodes_deduplicated
    hypothesis = "Estela's frequent requests for reassurance are due to her anxious attachment style"  # TODO: Get from somewhere

    G = nx.DiGraph()
    for row in df.iter_rows(named=True):
        G.add_node(
            row["id"],
            description=row["proposition"],
            frequency=row["frequency"],
            user=row["user"],
            datetime=get_node_datetime(row["datetimes"]),
            chunk_ids=row["chunk_ids"],
        )
        G.add_edges_from([(row["id"], e) for e in row["edges"]])

    label_embeddings = df.select("id", "embedding").to_dicts()

    result, trace = graph_explorer_agent.validate_hypothesis(
        hypothesis,
        actions_impl=ActionsImpl(
            get_similar_nodes=lambda query: get_similar_nodes(
                G, label_embeddings, batch_embedder, query
            ),
            get_causal_chain=lambda node_id1, node_id2: get_causal_chain(
                G, node_id1, node_id2
            ),
            get_causes=lambda node_id: get_parents(G, node_id),
            get_effects=lambda node_id, depth: get_children(G, node_id, depth),
        ),
    )

    context.log.info(f"Result: {result}")

    total_cost = sum(float(t.cost) if t.cost else 0 for t in trace) if trace else 0

    context.log.info(f"Total cost: {total_cost}")

    return trace
