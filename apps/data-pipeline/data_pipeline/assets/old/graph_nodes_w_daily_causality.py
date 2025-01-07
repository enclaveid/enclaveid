from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource


def get_cross_conversation_relationships_prompt(inferrables_groups: list[dict]) -> str:
    formatted_groups = "\n\n".join(
        f"Conversation {i + 1} (Date: {group['date']}):\n"
        + "\n".join(
            f"- {item['description']} (Label: {item['label']})"
            for item in group["inferrables"]
        )
        for i, group in enumerate(inferrables_groups)
    )

    return dedent(
        f"""
        Analyze these groups of inferrable claims from different conversations and identify causal relationships between them.
        Focus on how claims from one conversation might influence or relate to claims in other conversations.

        {formatted_groups}

        Generate ONLY causal relationships BETWEEN different conversations (not within the same conversation).
        Return the relationships in this JSON format:
        [
          {{
            "source": "SOURCE_LABEL",
            "target": "TARGET_LABEL"
          }}
        ]

        Rules:
        - Only create relationships between items from different conversations
        - Focus on strong, logical causal connections
        - Use the exact labels provided
        - Return empty array if no clear cross-conversation relationships exist
        """
    ).strip()


def parse_causal_relationships(text: str) -> list[dict]:
    try:
        relationships = repair_json(text, return_objects=True)
        if isinstance(relationships, list) and all(
            isinstance(r, dict) and "source" in r and "target" in r
            for r in relationships
        ):
            return relationships
        return []
    except Exception:
        return []


class DailyCausalityConfig(RowLimitConfig):
    window_size: int = Field(
        default=10,
        description="The number of conversations to analyze at a time",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "graph_nodes": AssetIn(
            key=["graph_nodes"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def graph_nodes_w_daily_causality(
    context: AssetExecutionContext,
    config: DailyCausalityConfig,
    llama70b: BaseLlmResource,
    graph_nodes: pl.DataFrame,
):
    logger = context.log

    # Group inferrables by conversation_id and date
    inferrables_df = (
        graph_nodes.filter(pl.col("category") == "inferrable")
        .sort("date")
        .select(
            ["conversation_id", "date", "label", "description", "causal_relationships"]
        )
    )

    # First group by date
    dates = inferrables_df.get_column("date").unique().sort()

    # Prepare data structure to collect all prompts and track conversation groups
    all_prompts = []
    conversation_group_mapping = []  # To map completion indices back to conversation groups
    new_relationships = {}

    # Collect all prompts first
    for date in dates:
        # Get conversations for this date
        date_conversations = (
            inferrables_df.filter(pl.col("date") == date)
            .unique(subset=["conversation_id"])
            .get_column("conversation_id")
            .to_list()
        )

        # Create groups of conversations within this date
        conversation_groups = [
            date_conversations[i : i + config.window_size]
            for i in range(0, len(date_conversations), config.window_size)
        ]

        for conv_group in conversation_groups:
            group_data = []
            for conv_id in conv_group:
                conv_inferrables = (
                    inferrables_df.filter(
                        (pl.col("conversation_id") == conv_id)
                        & (pl.col("date") == date)
                    )
                    .select(["label", "description"])
                    .to_dicts()
                )

                group_data.append(
                    {
                        "date": date,
                        "conversation_id": conv_id,
                        "inferrables": conv_inferrables,
                    }
                )

            # Add prompt to batch
            prompt = get_cross_conversation_relationships_prompt(group_data)
            all_prompts.append([prompt])
            conversation_group_mapping.append((date, conv_group))

    # Send all prompts in a single batch
    logger.info(f"Sending batch of {len(all_prompts)} prompts...")
    completions, total_cost = llama70b.get_prompt_sequences_completions_batch(
        all_prompts
    )
    logger.info(f"Analysis cost: ${total_cost:.2f}")

    # Process all completions
    for i, completion in enumerate(completions):
        if not completion:
            continue

        date, conv_group = conversation_group_mapping[i]
        relationships = parse_causal_relationships(completion[-1])

        # Store relationships for each affected conversation
        for rel in relationships:
            for conv_id in conv_group:
                conv_labels = set(
                    inferrables_df.filter(
                        (pl.col("conversation_id") == conv_id)
                        & (pl.col("date") == date)
                    ).get_column("label")
                )

                if rel["source"] in conv_labels or rel["target"] in conv_labels:
                    if conv_id not in new_relationships:
                        new_relationships[conv_id] = []
                    new_relationships[conv_id].append(rel)

    # Add new relationships to each row that matches the labels
    def update_relationships(row):
        conv_id = row["conversation_id"]
        label = row["label"]
        existing_relationships = row["causal_relationships"]

        if conv_id not in new_relationships:
            return existing_relationships

        # Only append relationships where this row's label is involved
        new_rels = [
            rel
            for rel in new_relationships[conv_id]
            if rel["source"] == label or rel["target"] == label
        ]

        return existing_relationships + new_rels

    # Update the relationships for each row
    result = graph_nodes.with_columns(
        causal_relationships=pl.struct(
            ["conversation_id", "label", "causal_relationships"]
        ).map_elements(update_relationships)
    )

    logger.info("Added cross-conversation relationships")
    return result
