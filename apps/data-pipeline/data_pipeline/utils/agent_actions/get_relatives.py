from typing import Literal

import igraph as ig

from data_pipeline.resources.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
    NodeReference,
)


def get_children(igraph: ig.Graph, node_id: str, depth: int) -> AdjacencyList:
    return _get_relatives(igraph, node_id, depth, mode="out")


def get_parents(igraph: ig.Graph, node_id: str, depth: int) -> AdjacencyList:
    return _get_relatives(igraph, node_id, depth, mode="in")


def _get_relatives(
    igraph: ig.Graph, node_id: str, depth: int, mode: Literal["in", "out"] = "out"
) -> AdjacencyList:
    # Get the vertex index for the given node_id
    try:
        vertex_idx = igraph.vs.find(name=node_id).index
    except ValueError:
        return []  # Return empty list if node not found

    # Get all ancestors/descendants up to specified depth using neighborhood()
    relatives = igraph.neighborhood(
        vertices=vertex_idx,
        order=depth,
        mode=mode,  # "in" for parents, "out" for children
        mindist=1,  # Exclude the start node itself
    )

    result: AdjacencyList = []

    # Process each relative
    for rel_idx in relatives[0]:  # [0] because neighborhood returns a list of lists
        rel_vertex = igraph.vs[rel_idx]
        parent_indices = igraph.predecessors(rel_idx)

        # Create parent references
        parents = [
            NodeReference(
                id=igraph.vs[parent_idx]["name"],
                datetime=igraph.vs[parent_idx].get("datetime", ""),
            )
            for parent_idx in parent_indices
        ]

        # Create children references
        child_indices = igraph.successors(rel_idx)
        children = [
            NodeReference(
                id=igraph.vs[child_idx]["name"],
                datetime=igraph.vs[child_idx].get("datetime", ""),
            )
            for child_idx in child_indices
        ]

        # Create record for this node
        record = AdjacencyListRecord(
            id=rel_vertex["name"],
            description=rel_vertex.get("description", ""),
            datetime=rel_vertex.get("datetime", ""),
            parents=parents,
            children=children,
        )

        result.append(record)

    return result
