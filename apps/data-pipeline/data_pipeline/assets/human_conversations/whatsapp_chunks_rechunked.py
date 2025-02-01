import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import user_partitions_def


class WhatsappChunksRechunkedConfig(Config):
    min_chunk_size: int = Field(default=10, description="The minimum size of a chunk")


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_sequential": AssetIn(
            key=["whatsapp_chunks_sequential"],
        ),
    },
)
def whatsapp_chunks_rechunked(
    context: AssetExecutionContext,
    config: WhatsappChunksRechunkedConfig,
    whatsapp_chunks_sequential: pl.DataFrame,
) -> pl.DataFrame:
    df = whatsapp_chunks_sequential

    # 1) Group by chunk_id to find how many rows each chunk has
    #    Also get the earliest datetime in each chunk for ordering.
    grouped = (
        df.group_by("chunk_id")
        .agg(
            [
                pl.count().alias("chunk_size"),
                pl.col("datetime").min().alias("earliest_dt"),
            ]
        )
        .sort("earliest_dt")
    )

    # Lists of chunk IDs and their sizes, in ascending order of earliest_dt
    chunk_ids = grouped["chunk_id"].to_list()
    chunk_sizes = dict(zip(grouped["chunk_id"], grouped["chunk_size"]))

    # We'll build a mapping old_id -> new_id
    # Initially, each chunk maps to itself
    new_chunk_ids = {cid: cid for cid in chunk_ids}

    # 2) Merge small chunks into their subsequent chunk
    i = 0
    # We'll mutate chunk_ids in place, removing ones that get merged
    while i < len(chunk_ids):
        current_id = chunk_ids[i]
        size = chunk_sizes[current_id]

        # If this chunk is too small and there is a next chunk, merge
        if size < config.min_chunk_size and i < len(chunk_ids) - 1:
            next_id = chunk_ids[i + 1]
            # Merge current chunk's size into next chunk
            chunk_sizes[next_id] += size
            chunk_sizes[current_id] = 0

            # Map current chunk -> next chunk
            new_chunk_ids[current_id] = next_id

            # Remove current chunk from the list of active chunks
            chunk_ids.pop(i)
            # Do NOT advance i, so we re-check the newly expanded chunk_ids[i]
            # on the next iteration (in case it's still < min_size).
        else:
            # This chunk is large enough, or it's the last chunk
            i += 1

    # 3) Flatten any mapping chains (e.g. if chunk1 -> chunk2, chunk2 -> chunk3)
    def find_final_id(cid):
        # Follow the chain until the mapping is id -> itself
        while new_chunk_ids[cid] != cid:
            cid = new_chunk_ids[cid]
        return cid

    for cid in list(new_chunk_ids.keys()):
        new_chunk_ids[cid] = find_final_id(cid)

    # 4) Create a new column in df that has the final chunk_id
    df = df.with_columns(
        pl.col("chunk_id")
        .map_elements(lambda old_id: new_chunk_ids[old_id])
        .alias("chunk_id")
    )

    return df
