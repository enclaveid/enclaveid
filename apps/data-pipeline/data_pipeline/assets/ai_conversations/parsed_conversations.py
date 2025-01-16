from datetime import datetime
from io import StringIO
from zipfile import ZipFile, is_zipfile

import pandas as pd
import polars as pl
from dagster import (
    AssetExecutionContext,
    Config,
    asset,
)

from data_pipeline.constants.environments import API_STORAGE_DIRECTORY, DataProvider
from data_pipeline.partitions import user_partitions_def


def _process_conversation_data(original_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process conversation data into a structured DataFrame with conversation_id,
    date, time, question and answer columns.

    Args:
        original_df (pd.DataFrame): DataFrame containing the mapping column
    Returns:
        pd.DataFrame: Processed conversation data
    """
    # Initialize lists to store the processed data
    processed_data = []

    # Iterate through each row in the original DataFrame
    for _, row in original_df.iterrows():
        conversation_id = row["id"]
        title = row["title"]
        mapping = row["mapping"]
        conversation_data = list(mapping.values())

        # Iterate through messages with index to check next message
        for i, message in enumerate(conversation_data):
            # Check if the message has required fields and is from a user
            if (
                message.get("message")
                and message["message"].get("author")
                and message["message"]["author"].get("role") == "user"
                and message["message"].get("create_time")
                and message["message"].get("content")
            ):
                # Extract timestamp and convert to datetime
                timestamp = message["message"]["create_time"]
                dt = datetime.fromtimestamp(timestamp)

                # Process question
                question_parts = message["message"]["content"].get("parts", [""])
                question_parts = [
                    str(part) if isinstance(part, dict) else part
                    for part in question_parts
                ]
                question = "\n".join(question_parts)

                # Get answer from next message if it exists and is from assistant
                answer = ""
                if i + 1 < len(conversation_data):
                    next_message = conversation_data[i + 1]
                    if (
                        next_message.get("message")
                        and next_message["message"].get("author")
                        and next_message["message"]["author"].get("role") == "assistant"
                        and next_message["message"].get("content")
                    ):
                        answer_parts = next_message["message"]["content"].get(
                            "parts", [""]
                        )
                        answer_parts = [
                            str(part) if isinstance(part, dict) else part
                            for part in answer_parts
                        ]
                        answer = "\n".join(answer_parts)

                processed_data.append(
                    {
                        "conversation_id": conversation_id,
                        "title": title,
                        "date": dt.date(),
                        "time": dt.time(),
                        "question": question,
                        "answer": answer,
                    }
                )

    # Create DataFrame from processed data
    df_conversations = pd.DataFrame(processed_data)

    # Sort by date and time
    df_conversations = df_conversations.sort_values(
        ["conversation_id", "date", "time"], ascending=[True, True, True]
    )

    return df_conversations


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
)
def parsed_conversations(
    context: AssetExecutionContext, config: Config
) -> pl.DataFrame:
    archive_path = (
        API_STORAGE_DIRECTORY
        / context.partition_key
        / DataProvider.OPENAI["path_prefix"]
        / "latest.zip"
    )

    expected_file = DataProvider.OPENAI["expected_file"]
    with archive_path.open("rb") as f:
        if not is_zipfile(f):
            raise ValueError("Expected a zip archive but got a different file type.")

        with ZipFile(f, "r") as zip_ref, zip_ref.open(expected_file) as zip_f:
            raw_df = pd.read_json(zip_f)

    if raw_df.empty:
        raise ValueError("Expected a non-empty DataFrame but got an empty one.")

    processed_df = _process_conversation_data(raw_df)

    # First we read it into a StringIO object with pandas since polars is a bit stricter
    # with the types
    csv_file = StringIO()
    processed_df.to_csv(csv_file, index=False)
    csv_file.seek(0)

    return pl.from_pandas(pd.read_csv(csv_file))
