from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
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
    summary_prompt_sequence=[
        lambda search_activity: (
            f"Here is a list of my recent Google search activity.\n{search_activity}\n"
            "Consider the possible usages of Google Search that do not deeply engage "
            "one's identity. Does this activity seem rather reactive and based on "
            "circumstance, or does it seem proactive and curiosity driven with a sense "
            "of purpose and direction? Answer YES in the first case, NO otherwise."
        ),
        (
            "If you answered NO: What can you learn about the user from this trend? Provide a general summary of"
            " the trend and a fine grained summary which includes specific niche topics that "
            " make this activity unique. \n"
            "If you answered YES: What kind of circumstances must the user have found themselves to prompt this"
            " activity? Include specific details on the circumstances."
        ),
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
    ins={
        "interests_clusters": AssetIn(
            key=["general_interests_clusters"],
        ),
    },
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
            general_interests_spec.summary_prompt_sequence[0](row["cluster_items"]),
            general_interests_spec.summary_prompt_sequence[1],
        ]
        for row in df.to_dicts()
    ]

    context.log.info(f"Processing {len(prompt_sequences)} clusters...")
    summaries_completions = await llama70b.get_prompt_sequences_completions(
        prompt_sequences
    )

    cluster_splits = list(map(lambda x: x[0], summaries_completions))

    # Tag the clusters with the type of activity: YES = reactive, NO = proactive
    activity_types = []
    for cluster_split in cluster_splits:
        if cluster_split is None:
            activity_types.append("unknown")
        else:
            if "YES" in cluster_split:
                activity_types.append("reactive")
            else:
                activity_types.append("proactive")

    cluster_summaries = list(map(lambda x: x[1], summaries_completions))

    return (
        df.with_columns(
            cluster_summary=pl.Series(cluster_summaries),
            activity_type=pl.Series(activity_types),
        )
        .filter(pl.col("activity_type") != "unknown")
        .drop(["cluster_items", "date_interests", "date", "interests"])
    )


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
        embeddings=pl.col("cluster_summary").map_batches(
            sentence_transformer.get_embeddings
        )
    )


@asset(
    partitions_def=user_partitions_def,
    deps=[general_summaries_embeddings],
    io_manager_key="parquet_io_manager",
    op_tags=k8s_gpu_config,
)
def general_user_matching(
    context: AssetExecutionContext,
    config: RowLimitConfig,
) -> pl.DataFrame:
    current_user_df = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET
        / "general_summaries_embeddings"
        / f"{context.partition_key}.snappy"
    ).sort(by="cluster_label")

    result_df = pl.DataFrame(
        {
            "user_cluster_label": pl.Series([], dtype=pl.Int64),
            "other_user_cluster_label": pl.Series([], dtype=pl.Int64),
            "cosine_similarity": pl.Series([], dtype=pl.Float64),
            "other_user_id": pl.Series([], dtype=pl.Utf8),
        }
    )

    # Get a list of ready partitions in the parent asset
    other_user_ids = context.instance.get_materialized_partitions(
        context.asset_key_for_input("general_summaries_embeddings")
    )

    context.log.info(f"Matching with {len(other_user_ids)-1} users")

    # TODO Optimization: Do not recompute the embeddings for the same pair of users
    for other_user_id in other_user_ids:
        if other_user_id == context.partition_key:
            continue

        other_user_df = pl.read_parquet(
            DAGSTER_STORAGE_BUCKET
            / "general_summaries_embeddings"
            / f"{other_user_id}.snappy"
        ).sort(by="cluster_label")

        # Perform the bipartite matching for each user
        match_df = maximum_bipartite_matching(
            current_user_df["embeddings"].to_numpy(),
            other_user_df["embeddings"].to_numpy(),
        )

        # Add the other_user_id to the match_df
        match_df = match_df.with_columns(
            other_user_id=pl.Series([other_user_id] * len(match_df))
        )

        result_df = result_df.vstack(match_df)

    return result_df.sort(by="cosine_similarity", descending=True)
