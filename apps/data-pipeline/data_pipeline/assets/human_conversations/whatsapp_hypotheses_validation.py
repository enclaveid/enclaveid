import json
from dataclasses import asdict

import networkx as nx
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.resources.graph_explorer_agent.agent import GraphExplorerAgent
from data_pipeline.resources.graph_explorer_agent.types import (
    ActionsImpl,
    HypothesisValidationResult,
    TraceRecord,
)
from data_pipeline.utils.agent_actions import (
    get_causal_chain,
    get_children,
    get_similar_nodes,
)
from data_pipeline.utils.agent_actions.get_relatives import (
    get_parents,
)
from data_pipeline.utils.get_node_datetime import get_node_datetime
from data_pipeline.utils.get_working_dir import get_working_dir


def _write_traces(traces: list[TraceRecord], context: AssetExecutionContext):
    working_dir = get_working_dir(context)
    working_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(traces).write_parquet(
        f"{working_dir}/{context.partition_key}.trace.snappy"
    )


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
    batch_embedder: BatchEmbedderResource,
    deepseek_r1: BaseLlmResource,
):
    llm_config = deepseek_r1.llm_config
    df = whatsapp_nodes_deduplicated

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

    result: HypothesisValidationResult | None = None
    traces: list[TraceRecord] = []

    while not result or result.decision == "refine":
        if not result:
            hypothesis = "Estela's frequent requests for reassurance are due to her anxious attachment style"  # TODO: Get from somewhere
        else:
            if not result.new_hypothesis:
                raise ValueError("No hypothesis provided")
            hypothesis = result.new_hypothesis
        try:
            result, trace = GraphExplorerAgent(llm_config).validate_hypothesis(
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
        except Exception as e:
            _write_traces(traces, context)
            raise e

        if not trace or not result:
            raise ValueError("No trace or result returned from agent")

        context.log.info(
            f"[INTERMEDIATE_RESULT] {json.dumps(asdict(result), indent=2)}"
        )

        traces.extend(trace)

    context.log.info(f"[FINAL_RESULT] {json.dumps(asdict(result), indent=2)}")

    total_cost = sum(float(t.cost) if t.cost else 0 for t in traces) if traces else 0
    context.log.info(f"Total cost: ${total_cost:.2f}")

    return pl.DataFrame(traces)
