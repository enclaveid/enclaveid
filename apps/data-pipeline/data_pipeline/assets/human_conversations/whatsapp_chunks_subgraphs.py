import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.get_messaging_partners import get_messaging_partners
from data_pipeline.utils.polars_expressions.messages_struct_to_string_format_expr import (
    get_messages_struct_to_string_format_expr,
)
from data_pipeline.utils.prompt_sequences.inferrables_extraction import (
    get_inferrables_extraction_prompt_sequence,
)


def parse_subgraphs(response: str) -> list[dict] | None:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, list):
            return [
                {
                    "id": node.get("id", None),
                    "datetime": node.get("datetime", None),
                    "proposition": node.get("proposition", None),
                    "caused_by": node.get("caused_by", []),
                    "caused": node.get("caused", []),
                }
                for node in res
            ]
        else:
            return None
    except Exception:
        return None


class WhatsappChunksSubgraphsConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_conversation_rechunked": AssetIn(
            key=["whatsapp_conversation_rechunked"],
        ),
    },
)
def whatsapp_chunks_subgraphs(
    context: AssetExecutionContext,
    whatsapp_conversation_rechunked: pl.DataFrame,
    gpt4o: BaseLlmResource,
    config: WhatsappChunksSubgraphsConfig,
):
    llm = gpt4o
    messaging_partners = get_messaging_partners()

    df = whatsapp_conversation_rechunked.with_columns(
        messages_str=get_messages_struct_to_string_format_expr(messaging_partners)
    ).slice(0, config.row_limit)

    prompt_sequences = [
        get_inferrables_extraction_prompt_sequence(
            messages_str, messaging_partners.me, messaging_partners.partner
        )
        for messages_str in df.get_column("messages_str").to_list()
    ]

    (
        completions,
        cost,
    ) = llm.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    context.log.info(f"Subgraphs extraction cost: ${cost:.6f}")

    (
        subgraphs_attributes,
        subgraphs_context,
        subgraphs_meta,
    ) = zip(
        *[
            (
                parse_subgraphs(completion[-1]),
                parse_subgraphs(completion[-2]),
                parse_subgraphs(completion[-3]),
            )
            if completion
            else (None, None, None)
            for completion in completions
        ]
    )

    return df.with_columns(
        subgraph_attributes=pl.Series(subgraphs_attributes, strict=False),
        subgraph_context=pl.Series(subgraphs_context, strict=False),
        subgraph_meta=pl.Series(subgraphs_meta, strict=False),
    )
