import numpy as np
import polars as pl


def get_raw_data(
    whatsapp_nodes_deduplicated: pl.DataFrame,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    node_id: str,
) -> str:
    df = whatsapp_nodes_deduplicated.filter(pl.col("id") == node_id)

    if df.is_empty():
        return ""

    chunk_ids = np.random.choice(np.unique(df.get_column("chunk_ids").item()), 1)

    return (
        whatsapp_chunks_subgraphs.filter(pl.col("chunk_id").eq(chunk_ids))
        .get_column("messages_str")
        .item()
    )


if __name__ == "__main__":
    print(
        get_raw_data(
            pl.read_parquet(
                "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_nodes_deduplicated/00393494197577/0034689896443.snappy"
            ),
            pl.read_parquet(
                "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_chunks_subgraphs/00393494197577/0034689896443.snappy"
            ),
            "giovanni_future_orientation_and_planning",
        )
    )
