from textwrap import dedent
from typing import Dict

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from json_repair import repair_json
from pydantic import Field

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.resources.postgres_resource import PostgresResource
from data_pipeline.utils.get_messaging_partners import get_messaging_partners
from data_pipeline.utils.graph.build_graph_from_df import build_graph_from_df
from data_pipeline.utils.graph.save_graph import save_graph
from data_pipeline.utils.super_deduplicator import deduplicate_nodes_dataframe


def _get_synthetization_prompt_sequence(
    text: str,
) -> PromptSequence:
    return [
        dedent(
            f"""
            Given a list of similar propositions, synthesize all propositions into a single proposition encompassing all of them.

            Provide your response in the following format:
            {{
                "proposition": "Synthesized proposition"
            }}

            Here is the list of propositions:
            {text}
            """
        ).strip()
    ]


def _parse_synthetization_response(response: str) -> str | None:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, dict):
            return res["proposition"]
        else:
            return None
    except Exception:
        return None


class WhatsappClaimsDeduplicatedConfig(Config):
    threshold: float = Field(
        default=0.95, description="Cosine similarity threshold for merging claims"
    )
    debug_graph: bool = Field(
        default=True, description="Whether to save the graph to the debug directory"
    )


def _make_ids_globally_unique(
    df: pl.DataFrame,
    used_ids: set[str],
    id_col: str = "id",
    rel_col: str = "relationships",
) -> pl.DataFrame:
    """
    Ensures IDs in df[id_col] are unique globally, by appending '_2', '_3', etc.
    Updates relationship references accordingly.
    """
    old_ids = df[id_col].to_list()
    # Build a mapping from old_id -> new_id
    id_mapping: Dict[str, str] = {}
    for old_id in old_ids:
        candidate = old_id
        counter = 2
        # If candidate is already taken, append _2, _3, etc.
        while candidate in used_ids:
            candidate = f"{old_id}_{counter}"
            counter += 1
        id_mapping[old_id] = candidate
        used_ids.add(candidate)

    # Replace the DataFrame's id column
    df = df.with_columns(pl.col(id_col).map_elements(lambda x: id_mapping[x]))

    # Update relationships so that old references get mapped to new IDs
    if rel_col in df.columns:
        df = df.with_columns(
            pl.col(rel_col).map_elements(
                lambda rels: [
                    {
                        "source": id_mapping.get(r["source"], r["source"]),
                        "target": id_mapping.get(r["target"], r["target"]),
                    }
                    for r in rels
                ]
            )
        )

    return df


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_node_embeddings": AssetIn(
            key=["whatsapp_node_embeddings"],
        ),
    },
)
async def whatsapp_nodes_deduplicated(
    context: AssetExecutionContext,
    config: WhatsappClaimsDeduplicatedConfig,
    whatsapp_node_embeddings: pl.DataFrame,
    postgres: PostgresResource,
    batch_embedder: BatchEmbedderResource,
    llama70b: BaseLlmResource,
) -> pl.DataFrame:
    messaging_partners = get_messaging_partners(
        postgres, context.partition_keys[0].split("|")
    )

    # Gather embeddings and find similarities
    df = whatsapp_node_embeddings

    # Determine "user" by which name(s) appear in the proposition
    df = df.with_columns(
        pl.when(
            pl.col("proposition").str.contains(
                f"{messaging_partners.initiator_name} and {messaging_partners.partner_name}|{messaging_partners.partner_name} and {messaging_partners.initiator_name}"
            )
        )
        .then(pl.lit("both"))
        .when(
            pl.col("proposition")
            .str.extract(
                f"({messaging_partners.initiator_name}|{messaging_partners.partner_name})",
                0,
            )
            .is_not_null()
        )
        .then(
            pl.col("proposition").str.extract(
                f"({messaging_partners.initiator_name}|{messaging_partners.partner_name})",
                0,
            )
        )
        .otherwise(pl.lit("both"))
        .alias("user")
    )

    df = df.with_columns(
        pl.when(
            (pl.col("caused").list.len() > 0) | (pl.col("caused_by").list.len() > 0)
        )
        .then(
            pl.struct(["id", "caused", "caused_by"]).map_elements(
                lambda row: (
                    [{"source": row["id"], "target": c} for c in row["caused"]]
                    +
                    # Relationships from items in caused_by -> this node
                    [{"source": c_by, "target": row["id"]} for c_by in row["caused_by"]]
                ),
                return_dtype=pl.List(
                    pl.Struct(
                        [pl.Field("source", pl.Utf8), pl.Field("target", pl.Utf8)]
                    )
                ),
            )
        )
        .otherwise(None)
        .alias("relationships")
    )

    deduplication_args = {
        "label_col": "id",
        "embedding_col": "embedding",
        "single_fields": ["user", "proposition", "embedding"],
        "list_fields": [
            ("ids", "id"),
            ("chunk_ids", "chunk_id"),
            ("datetimes", "datetime"),
            ("propositions", "proposition"),
            ("subgraph_types", "subgraph_type"),
        ],
        "relationship_col": "relationships",
        "threshold": config.threshold,
    }

    # Deduplicate by user group
    df_both = df.filter(pl.col("user") == "both")
    df_initiator = df.filter(pl.col("user") == messaging_partners.initiator_name)
    df_partner = df.filter(pl.col("user") == messaging_partners.partner_name)

    deduped_both = deduplicate_nodes_dataframe(df_both, **deduplication_args)
    deduped_initiator = deduplicate_nodes_dataframe(df_initiator, **deduplication_args)
    deduped_partner = deduplicate_nodes_dataframe(df_partner, **deduplication_args)

    # Make IDs globally unique across the three dataframes
    used_ids: set[str] = set()

    deduped_both = _make_ids_globally_unique(deduped_both, used_ids)
    deduped_initiator = _make_ids_globally_unique(deduped_initiator, used_ids)
    deduped_partner = _make_ids_globally_unique(deduped_partner, used_ids)

    # Combine them
    deduplicated_df = pl.concat(
        [deduped_both, deduped_initiator, deduped_partner],
        how="vertical",
    ).with_row_count("index")

    # Synthesize propositions for rows with frequency > 1
    to_synthesize = (
        deduplicated_df.filter(pl.col("frequency") > 1)
        .select("index", "propositions")
        .with_columns(propositions_str=pl.col("propositions").list.join("\n"))
    )

    prompt_sequences = [
        _get_synthetization_prompt_sequence(row["propositions_str"])
        for row in to_synthesize.iter_rows(named=True)
    ]
    completions, cost = llama70b.get_prompt_sequences_completions_batch(
        prompt_sequences
    )
    context.log.info(f"Synthesization cost: ${cost:.6f}")

    propositions = [
        _parse_synthetization_response(completion[-1]) if completion else None
        for completion in completions
    ]
    to_synthesize = to_synthesize.with_columns(
        proposition=pl.Series(propositions),
    ).drop("propositions_str")

    # Embed new synthesized propositions
    cost, embeddings = await batch_embedder.get_embeddings(
        to_synthesize.get_column("proposition").to_list(),
    )
    context.log.info(f"Embedding cost: ${cost:.6f}")
    to_synthesize = to_synthesize.with_columns(embedding=pl.Series(embeddings))

    deduplicated_df = deduplicated_df.join(
        to_synthesize, on="index", how="left", suffix="_right"
    ).sort("frequency", descending=True)

    cols_to_coalesce = [
        col.replace("_right", "")
        for col in deduplicated_df.columns
        if col.endswith("_right")
    ]
    deduplicated_df = (
        deduplicated_df.with_columns(
            [
                pl.col(f"{col}_right").fill_null(pl.col(col)).alias(col)
                for col in cols_to_coalesce
            ]
        )
        .drop([col + "_right" for col in cols_to_coalesce])
        .drop("index")
    )

    if config.debug_graph:
        save_graph(
            build_graph_from_df(
                deduplicated_df,
                "relationships",
                "id",
                ["frequency", "user", "proposition"],
            ),
            context,
        )

    return deduplicated_df.drop("propositions", "ids")
