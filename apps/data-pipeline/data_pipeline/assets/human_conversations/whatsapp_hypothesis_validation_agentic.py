import igraph as ig
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.graph_explorer_agent.resource import (
    GraphExplorerAgentResource,
)
from data_pipeline.resources.graph_explorer_agent.types import ActionsImpl
from data_pipeline.utils.agent_actions import (
    connect_nodes,
    get_causal_chain,
    get_children,
    get_parents,
    get_similar_nodes,
)


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_causal_graph": AssetIn(
            key=["whatsapp_causal_graph"],
        ),
    },
)
def whatsapp_hypothesis_validation_agentic(
    context: AssetExecutionContext,
    whatsapp_causal_graph: pl.DataFrame,
    graph_explorer_agent: GraphExplorerAgentResource,
):
    hypothesis = "The user is a customer"  # TODO: Get from somewhere

    igraph = ig.Graph(whatsapp_causal_graph)

    result, trace = graph_explorer_agent.validate_hypothesis(
        hypothesis,
        actions_impl=ActionsImpl(
            get_similar_nodes=lambda query: get_similar_nodes(
                whatsapp_causal_graph, query
            ),
            get_causal_chain=lambda node_id, target_node_id: get_causal_chain(
                whatsapp_causal_graph, node_id, target_node_id
            ),
            get_parents=lambda node_id, depth: get_parents(igraph, node_id, depth),
            get_children=lambda node_id, depth: get_children(igraph, node_id, depth),
            connect_nodes=lambda node_id, target_node_id: connect_nodes(
                igraph, node_id, target_node_id
            ),
        ),
    )

    context.log.info(f"Result: {result}")

    total_cost = sum(float(t.cost) if t.cost else 0 for t in trace) if trace else 0
    context.log.info(f"Total cost: {total_cost}")

    return trace
