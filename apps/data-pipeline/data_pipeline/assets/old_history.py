from typing import TYPE_CHECKING, Dict

import numpy as np
import polars as pl
from dagster import (
    AllPartitionMapping,
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.resources.llm_inference.llama70b_resource import Llama70bResource
from data_pipeline.resources.llm_inference.sentence_transformer_resource import (
    SentenceTransformerResource,
)
from data_pipeline.utils.maximum_bipartite_matching import maximum_bipartite_matching

from ..constants.custom_config import RowLimitConfig
from ..constants.k8s import k8s_gpu_config
from ..partitions import user_partitions_def
from ..utils.is_cuda_available import is_cuda_available
from ..utils.old_history_utils import (
    InterestsSpec,
    get_full_history_sessions,
)

if is_cuda_available() or TYPE_CHECKING:
    import cuml
    import cupy as cp
    from cuml.cluster.hdbscan import HDBSCAN


general_interests_spec = InterestsSpec(
    name_prefix="general",
    enrichment_prompt_sequence=[
        (
            "Here is a list of my recent Google search activity. "
            "What have I been doing? What were my goals?"
        ),
        (
            "Format the previous answer as a semicolon-separated array of strings delimited by square brackets. "
            "Focus on the goal of the search activity in realtion to the specific topic."
        ),
    ],
    clustering_prompt_sequence=[
        (
            "Here is a list of records of some of my internet activity surrounding a specific topic."
            " What have I been doing? How are these activities related?"
        ),
        "How would you summarize this trajectory? Be mindful of the time periods.",
    ],
)


class InterestsConfig(RowLimitConfig):
    ml_model_name: str = Field(
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        description=(
            "The Hugging Face model to use as the LLM. See the vLLMs docs for a "
            "list of the support models:\n"
            "https://docs.vllm.ai/en/latest/models/supported_models.html"
        ),
    )

    chunk_size: int = Field(
        default=15,
        description=(
            "Split the raw history into chunks of this size. We allow vLLM to "
            "determine the ideal batch size by itsef, so this has no impact on "
            "runtime but it still determines how many records are shown to the "
            "LLM at one time. Having too many records can cause the LLM to give "
            "sub-par responses."
        ),
    )


class InterestsEmbeddingsConfig(RowLimitConfig):
    ml_model_name: str = Field(
        default="Salesforce/SFR-Embedding-2_R",
        description=("The Hugging Face model to use with SentenceTransformers."),
    )

    chunk_size: int = Field(
        default=15,
        description=(
            "Split the raw history into chunks of this size. We allow vLLM to "
            "determine the ideal batch size by itsef, so this has no impact on "
            "runtime but it still determines how many records are shown to the "
            "LLM at one time. Having too many records can cause the LLM to give "
            "sub-par responses."
        ),
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    op_tags=k8s_gpu_config,
)
def general_interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    llama8b: Llama8bResource,
    full_takeout: pl.DataFrame,
) -> pl.DataFrame:
    full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

    sessions_output = get_full_history_sessions(
        full_takeout=full_takeout,
        chunk_size=config.chunk_size,
        first_instruction=general_interests_spec.enrichment_prompt_sequence[0],
        second_instruction=general_interests_spec.enrichment_prompt_sequence[1],
        llama8b=llama8b,
    )

    context.add_output_metadata(
        {"count_invalid_responses": sessions_output.count_invalid_responses}
    )

    return sessions_output.output_df


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests": AssetIn(key=["general_interests"])},
    op_tags=k8s_gpu_config,
)
def general_interests_embeddings(
    context: AssetExecutionContext,
    config: InterestsEmbeddingsConfig,
    sentence_transformer: SentenceTransformerResource,
    interests: pl.DataFrame,
) -> pl.DataFrame:
    df = (
        # Enforce row_limit (if any)
        interests.slice(0, config.row_limit)
        .select("date", "interests")
        # Explode the interests so we get the embeddings for each individual interest
        .explode("interests")
        .drop_nulls()
    )

    context.log.info("Computing embeddings")
    return df.with_columns(
        embeddings=pl.col("interests").map_batches(sentence_transformer.get_embeddings)
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_embeddings": AssetIn(key=["general_interests_embeddings"])},
    op_tags=k8s_gpu_config,
)
def general_interests_clusters(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    interests_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    # Apply the row limit (if any)
    df = interests_embeddings.slice(0, config.row_limit)

    # Convert the embeddings to a CuPy array
    embeddings_gpu = cp.asarray(df["embeddings"].to_numpy())

    # Reduce the embeddings dimensions
    umap_model = cuml.UMAP(
        n_neighbors=15, n_components=100, min_dist=0.1, metric="cosine"
    )
    reduced_data_gpu = umap_model.fit_transform(embeddings_gpu)

    clusterer = HDBSCAN(
        min_cluster_size=10,
        gen_min_span_tree=True,
        metric="euclidean",
        # By specifying an epsilon we can coalesce similar clusters but we rather keep
        # them separate until after the bipartite matching stage
        # cluster_selection_epsilon=0.15,
    )
    cluster_labels = clusterer.fit_predict(reduced_data_gpu.astype(np.float64).get())

    cluster_stats = np.unique(cluster_labels, return_counts=True)

    context.add_output_metadata(
        {
            "clusters_count": len(cluster_stats[0]),
            "noise_count": int(cluster_stats[1][0]) if -1 in cluster_stats[0] else 0,
        }
    )

    # Remove the embeddings to save space
    return df.with_columns(cluster_label=pl.Series(cluster_labels)).drop("embeddings")


# TODO: add constraints to the llama70b resource to limit concurrency
@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests_clusters": AssetIn(key=["general_interests_clusters"])},
)
async def general_cluster_summaries(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    llama70b: Llama70bResource,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
    df = (
        interests_clusters.with_columns(
            (pl.col("date") + pl.lit(":") + pl.col("interests")).alias("date_interests")
        )
        .group_by("cluster_label")
        .agg([pl.col("date_interests").str.concat("\n").alias("cluster_items")])
        .filter(pl.col("cluster_label") != -1)
    )

    prompt_sequences = [
        [
            f"{general_interests_spec.clustering_prompt_sequence[0]}\n{row['cluster_items']}",
            general_interests_spec.clustering_prompt_sequence[1],
        ]
        for row in df.to_dicts()
    ]

    context.log.info(f"Processing {len(prompt_sequences)} clusters...")
    cluster_summaries = await llama70b.get_prompt_sequences_completions(
        prompt_sequences
    )

    return df.with_columns(
        cluster_summary=pl.Series(cluster_summaries),
    ).drop(["cluster_items", "date_interests", "date", "interests"])


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"cluster_summaries": AssetIn(key=["general_cluster_summaries"])},
    op_tags=k8s_gpu_config,
)
def general_summaries_embeddings(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    sentence_transformer: SentenceTransformerResource,
    cluster_summaries: pl.DataFrame,
) -> pl.DataFrame:
    df = cluster_summaries.slice(0, config.row_limit)

    context.log.info("Computing embeddings...")
    return df.with_columns(
        embeddings=pl.col("cluster_embeddings").map_batches(
            sentence_transformer.get_embeddings
        )
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "general_summaries_embeddings": AssetIn(
            partition_mapping=AllPartitionMapping(),
        )
    },
    op_tags=k8s_gpu_config,
)
def general_user_matching(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    general_summaries_embeddings: Dict[str, pl.DataFrame],
) -> pl.DataFrame:
    current_user_df = general_summaries_embeddings[context.partition_key].sort(
        by="cluster_label"
    )
    result_df = pl.DataFrame(
        {
            "other_user_id": [],
            "user_cluster_label": [],
            "other_user_cluster_label": [],
            "cosine_similarity": [],
        }
    )

    # TODO Optimization: Do not recompute the embeddings for the same pair of users
    for other_user_id, other_user_df in general_summaries_embeddings.items():
        if other_user_id == context.partition_key:
            continue

        other_user_df = other_user_df.sort(by="cluster_label")

        # Perform the bipartite matching for each user
        match_df = maximum_bipartite_matching(
            current_user_df["cluster_embeddings"].to_numpy(),
            other_user_df["cluster_embeddings"].to_numpy(),
        )

        # Add the other_user_id to the match_df
        match_df["other_user_id"] = other_user_id

        result_df = result_df.vstack(match_df)

    return result_df
