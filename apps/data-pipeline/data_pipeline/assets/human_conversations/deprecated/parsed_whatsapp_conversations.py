from collections import defaultdict
from zipfile import ZipFile, is_zipfile

import polars as pl
from dagster import AssetExecutionContext, asset

from data_pipeline.constants.environments import API_STORAGE_DIRECTORY, DataProvider
from data_pipeline.partitions import phone_number_partitions_def
from data_pipeline.resources.postgres_resource import PostgresResource

MESSAGE_MEDIA_TYPES = defaultdict(
    lambda: None,
    {
        1: "IMAGE",
        38: "SEE_ONCE_IMAGE",
        6: "SEE_ONCE_IMAGE",
        2: "VIDEO",
        39: "SEE_ONCE_VIDEO",
        13: "SEE_ONCE_VIDEO",
        3: "AUDIO",
        4: "CONTACT",
        5: "LOCATION",
        7: "URL",
        8: "FILE",
        11: "GIF",
        14: "DELETED_MESSAGE",
        15: "STICKER",
        46: "POLL",
        54: "VIDEO_NOTE",
    },
)


def _process_row(row: dict) -> str:
    text = row["content"]
    message_type = row["message_type"]
    media_title = row["media_title"]

    # If text is empty, try to get the media type
    if not text and message_type:
        text = f"MEDIA: {MESSAGE_MEDIA_TYPES.get(message_type, 'UNKNOWN')}"

    # If the text contains a link and media_title is not empty, replace the full URL with the media title
    if "https://" in text and media_title:
        # Find the start of the URL
        url_start = text.find("https://")
        # Find the end of the URL (space or end of string)
        url_end = text.find(" ", url_start)
        if url_end == -1:  # URL is at the end of the text
            url_end = len(text)
        # Replace the full URL with the media title
        text = text[:url_start] + "Sent a link: " + media_title + text[url_end:]

    return text


@asset(
    partitions_def=phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
)
def parsed_whatsapp_conversations(
    context: AssetExecutionContext, postgres: PostgresResource
) -> pl.DataFrame:
    # TODO: get user_id from phone_number (partition_key)
    # user_id = postgres.get_user_id(context.partition_key)
    user_id = "cm0i27jdj0000aqpa73ghpcxf"

    archive_path = (
        API_STORAGE_DIRECTORY
        / user_id
        / DataProvider.WHATSAPP_DESKTOP["path_prefix"]
        / "latest.zip"
    )

    expected_file = DataProvider.WHATSAPP_DESKTOP["expected_file"]
    with archive_path.open("rb") as f:
        if not is_zipfile(f):
            raise ValueError("Expected a zip archive but got a different file type.")

        with ZipFile(f, "r") as zip_ref, zip_ref.open(expected_file) as zip_f:
            raw_df = pl.read_json(zip_f.read())

    if raw_df.is_empty():
        raise ValueError("Expected a non-empty DataFrame but got an empty one.")

    processed_df = (
        (
            raw_df.select(
                pl.col("from"),
                pl.col("to"),
                pl.col("datetime"),
                pl.struct(
                    [
                        pl.col("content"),
                        pl.col("message_type"),
                        pl.col("media_title"),
                    ]
                ).alias("row"),
            )
            .with_columns(
                [
                    pl.col("row").map_elements(_process_row),
                ]
            )
            .rename({"row": "content"})
        )
        .with_columns(pl.col("datetime").str.strptime(pl.Datetime).alias("datetime"))
        .sort("datetime")
    )

    # Squash consecutive identical messages within the same conversation
    squashed_df = (
        processed_df.sort(["from", "to", "datetime"])
        .with_columns(
            [
                (
                    (pl.col("content") != pl.col("content").shift(1))
                    | (pl.col("from") != pl.col("from").shift(1))
                    | (pl.col("to") != pl.col("to").shift(1))
                )
                .cum_sum()
                .alias("message_group")
            ]
        )
        .group_by(["from", "to", "content", "message_group"])
        .agg(
            [
                pl.col("datetime").min(),
                pl.when(pl.count() > 1)
                .then(
                    pl.concat_str(
                        pl.lit("Sent "),
                        pl.count(),
                        pl.lit(" of "),
                        pl.col("content"),
                    )
                )
                .otherwise(pl.col("content"))
                .unique()
                .first()
                .alias("squashed_content"),
            ]
        )
        .drop(["message_group", "content"])
        .rename({"squashed_content": "content"})
    )

    return squashed_df
