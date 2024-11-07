import polars as pl
import ray
from dagster_pipes import PipesContext, open_dagster_pipes

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.embeddings.nvembed_resource import NVEmbedResource


@ray.remote(num_gpus=1)
def process_chunk(chunk_df, model):
    chunk_embeddings, cost = model.get_embeddings(chunk_df["summary"])
    return chunk_df.with_columns(summaries_embedding=chunk_embeddings), cost


def run_distributed_embeddings(
    context: PipesContext,
    embedder: NVEmbedResource,
    conversation_summaries: pl.DataFrame,
):
    embedder_ref = ray.put(embedder)
    context.log.info("Placed embedder in Ray object store")

    # Split dataframe into 4 chunks
    chunk_size = len(conversation_summaries) // 4
    chunks = [
        conversation_summaries.slice(i * chunk_size, chunk_size) for i in range(4)
    ]

    # Process chunks in parallel
    futures = [process_chunk.remote(chunk, embedder_ref) for chunk in chunks]

    # Gather results
    results = ray.get(futures)
    total_cost = 0
    processed_chunks = []

    for df_chunk, cost in results:
        processed_chunks.append(df_chunk)
        total_cost += cost

    # Combine results
    final_df = pl.concat(processed_chunks)

    context.log.info(f"Total embeddings cost: ${total_cost:.2f}")

    return final_df


if __name__ == "__main__":
    context = open_dagster_pipes()
    embedder = NVEmbedResource()
    embedder.setup_for_execution(None)
    conversation_summaries = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET
        / "conversation_summaries"
        / f"{context.partition_key}.snappy"
    )
    run_distributed_embeddings(context, embedder, conversation_summaries)
