import networkx as nx
from dagster import AssetExecutionContext

from data_pipeline.utils.get_working_dir import get_working_dir


def save_graph(G: nx.DiGraph, context: AssetExecutionContext):
    working_dir = get_working_dir(context)
    working_dir.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, f"{working_dir}/{context.partition_key}.graphml")
