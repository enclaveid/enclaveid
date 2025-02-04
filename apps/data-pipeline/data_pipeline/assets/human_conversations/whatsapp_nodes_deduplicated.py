from textwrap import dedent

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
            Provide a label in snake_case for the synthesized proposition.

            Provide your response in the following format:
            {{
                "proposition": "Synthesized proposition",
                "label": "a_label_for_the_synthesized_proposition",
            }}

            Here is the list of propositions:
            {text}
            """
        ).strip()
    ]


def _parse_synthetization_response(
    response: str
) -> tuple[str, str] | tuple[None, None]:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, dict):
            return res["proposition"], res["label"]
        else:
            return None, None
    except Exception:
        return None, None


class WhatsappClaimsDeduplicatedConfig(Config):
    threshold: float = Field(
        default=0.95, description="Cosine similarity threshold for merging claims"
    )
    debug_graph: bool = Field(
        default=True, description="Whether to save the graph to the debug directory"
    )


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

    # Add a user column based on the contents of the proposition column
    df = df.with_columns(
        pl.when(
            # Check if both names appear in either order using regex
            pl.col("proposition").str.contains(
                f"{messaging_partners.initiator_name} and {messaging_partners.partner_name}|{messaging_partners.partner_name} and {messaging_partners.initiator_name}"
            )
        )
        .then(pl.lit("both"))
        # Check which name appears first and use that
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

    # Create a relationship column
    df = df.with_columns(
        pl.when(
            (pl.col("caused").list.len() > 0) | (pl.col("caused_by").list.len() > 0)
        )
        .then(
            # Build a new list of relationship dicts for each row
            pl.struct(["id", "caused", "caused_by"]).map_elements(
                lambda row: (
                    # Relationships from this node -> items in caused
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
        ],
        "relationship_col": "relationships",
        "threshold": config.threshold,
    }

    # Deduplicate within user groups
    deduplicated_df = pl.concat(
        [
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == "both"), **deduplication_args
            ),
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == messaging_partners.initiator_name),
                **deduplication_args,
            ),
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == messaging_partners.partner_name),
                **deduplication_args,
            ),
        ],
        how="vertical",
    ).with_row_count("index")  # For joining later

    # Synthesize propositions
    synthesized_df = (
        deduplicated_df.filter(pl.col("frequency") > 1)
        .select("index", "propositions")
        .with_columns(propositions_str=pl.col("propositions").list.join("\n"))
    )
    prompt_sequences = [
        _get_synthetization_prompt_sequence(row["propositions_str"])
        for row in synthesized_df.iter_rows(named=True)
    ]

    completions, cost = llama70b.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"Synthesization cost: ${cost:.6f}")

    propositions, labels = zip(
        *(
            _parse_synthetization_response(completion[-1])
            if completion
            else (None, None)
            for completion in completions
        )
    )

    # Add back propositions and labels to synthesized_df
    synthesized_df = synthesized_df.with_columns(
        proposition=pl.Series(propositions),
        id=pl.Series(labels),
    ).drop("propositions_str")

    # Get embeddings
    cost, embeddings = await batch_embedder.get_embeddings(
        synthesized_df.get_column("proposition").to_list(),
    )

    context.log.info(f"Embedding cost: ${cost:.6f}")

    # Add embeddings to synthesized_df
    synthesized_df = synthesized_df.with_columns(embedding=pl.Series(embeddings))

    # Join back with deduplicated_df
    deduplicated_df = deduplicated_df.join(
        synthesized_df, on="index", how="left", suffix="_right"
    ).sort("frequency", descending=True)

    # Coalesce right columns with originals
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
