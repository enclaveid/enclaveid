import json
from dataclasses import asdict

import networkx as nx
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.agents.base_agent import TraceRecord
from data_pipeline.utils.agents.graph_explorer_agent.actions import (
    get_causal_chain,
    get_children,
    get_similar_nodes,
)
from data_pipeline.utils.agents.graph_explorer_agent.actions.get_raw_data import (
    get_raw_data,
)
from data_pipeline.utils.agents.graph_explorer_agent.actions.get_relatives import (
    get_parents,
)
from data_pipeline.utils.agents.graph_explorer_agent.graph_explorer_agent import (
    GraphExplorerAgent,
)
from data_pipeline.utils.agents.graph_explorer_agent.types import (
    ActionsImpl,
    HypothesisValidationResult,
)
from data_pipeline.utils.get_node_datetime import get_node_datetime


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_nodes_deduplicated": AssetIn(
            key=["whatsapp_nodes_deduplicated"],
        ),
        "whatsapp_chunks_subgraphs": AssetIn(
            key=["whatsapp_chunks_subgraphs"],
        ),
        "whatsapp_seed_hypotheses": AssetIn(
            key=["whatsapp_seed_hypotheses"],
        ),
    },
)
def whatsapp_hypotheses_validation(
    context: AssetExecutionContext,
    whatsapp_nodes_deduplicated: pl.DataFrame,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    whatsapp_seed_hypotheses: pl.DataFrame,
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

    def _validate_hypothesis(
        initial_hypothesis: str,
    ) -> dict[str, list[HypothesisValidationResult] | list[TraceRecord]]:
        traces = []
        results = []
        current_result = None
        while not current_result or current_result.decision == "refine":
            if not current_result:
                hypothesis_to_validate = initial_hypothesis
            else:
                context.log.info(
                    f"[INTERMEDIATE_RESULT] {json.dumps(asdict(current_result), indent=2)}"
                )

                if not current_result.new_hypothesis:
                    raise ValueError("No hypothesis provided")

                hypothesis_to_validate = current_result.new_hypothesis

            try:
                current_result, trace = GraphExplorerAgent(
                    llm_config
                ).validate_hypothesis(
                    hypothesis_to_validate,
                    actions_impl=ActionsImpl(
                        get_similar_nodes=lambda query: get_similar_nodes(
                            G,
                            label_embeddings,
                            batch_embedder,
                            query,
                            use_lock=get_environment() == "LOCAL",
                        ),
                        get_causal_chain=lambda node_id1, node_id2: get_causal_chain(
                            G, node_id1, node_id2
                        ),
                        get_causes=lambda node_id: get_parents(G, node_id),
                        get_effects=lambda node_id, depth: get_children(
                            G, node_id, depth
                        ),
                        get_raw_data=lambda node_id: get_raw_data(
                            whatsapp_nodes_deduplicated,
                            whatsapp_chunks_subgraphs,
                            node_id,
                        ),
                    ),
                )
            except Exception as e:
                context.log.error(f"Error validating hypothesis: {e}")
                return {"results": results, "traces": traces}

            if not trace or not current_result:
                context.log.error("No trace or result returned from agent")
                return {"results": results, "traces": traces}

            results.append(asdict(current_result))
            traces.extend([asdict(t) for t in trace])

        res = {"results": results, "traces": traces}
        context.log.info(f"[FINAL_RESULT] {json.dumps(res, indent=2)}")
        return res

    results_df = (
        whatsapp_seed_hypotheses.select(
            pl.struct("chunk_id", "hypothesis").alias("row")
        )
        .with_columns(
            validation_struct=pl.col("row").map_elements(
                lambda row: _validate_hypothesis(row["hypothesis"]),
                strategy="threading",
                return_dtype=pl.Struct(
                    [
                        pl.Field(
                            "results",
                            pl.List(
                                pl.Struct(
                                    [
                                        pl.Field("decision", pl.String),
                                        pl.Field("explanation", pl.String),
                                        pl.Field("new_hypothesis", pl.String),
                                    ]
                                )
                            ),
                        ),
                        pl.Field(
                            "traces",
                            pl.List(
                                pl.Struct(
                                    [
                                        pl.Field("role", pl.String),
                                        pl.Field("content", pl.String),
                                        pl.Field("reasoning_content", pl.String),
                                        pl.Field("cost", pl.Float64),
                                        pl.Field("token_count", pl.Int64),
                                        pl.Field("timestamp", pl.Float64),
                                    ]
                                )
                            ),
                        ),
                    ]
                ),
            )
        )
        .unnest("validation_struct", "row")
    )

    total_cost = (
        results_df.select("traces")
        .explode("traces")
        .select(pl.col("traces").map_elements(lambda t: t["cost"]).sum())
        .item()
    )
    context.log.info(f"Total cost: ${total_cost:.2f}")

    return results_df
