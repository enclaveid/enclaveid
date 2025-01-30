from typing import List

import networkx as nx
import polars as pl


def build_graph_from_df(
    df: pl.DataFrame,
    relationships_col: str,
    label_column: str,
    metadata_columns: List[str],
) -> nx.DiGraph:
    G = nx.DiGraph()

    # Add nodes with metadata
    for row in df.iter_rows(named=True):
        node_id = row[label_column]
        # Create node attributes dictionary from metadata columns
        node_attrs = {col: row[col] for col in metadata_columns if col in row}
        G.add_node(node_id, **node_attrs)

    # Add edges based on relationships
    for relationship in df[relationships_col].explode().drop_nulls().to_list():
        G.add_edge(relationship["source"], relationship["target"])

    return G
