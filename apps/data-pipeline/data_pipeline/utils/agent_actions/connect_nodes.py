import igraph as ig


def connect_nodes(igraph: ig.Graph, node_id: str, target_node_id: str) -> None:
    igraph.add_edge(node_id, target_node_id)

    return
