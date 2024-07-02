from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, AssetsDefinition, asset
from pydantic import Field

from ..constants.custom_config import RowLimitConfig
from ..constants.k8s import k8s_gpu_config
from ..partitions import user_partitions_def
from ..utils.is_cuda_available import is_cuda_available
from ..utils.old_history_utils import (
    InterestsSpec,
    get_embeddings,
    get_full_history_sessions,
)

if is_cuda_available() or TYPE_CHECKING:
    import cuml
    import cupy as cp
    from cuml.cluster.hdbscan import HDBSCAN
    from sentence_transformers import SentenceTransformer


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


def build_interests_assets(spec: InterestsSpec) -> list[AssetsDefinition]:
    @asset(
        name=spec.name_prefix + "_interests",
        partitions_def=user_partitions_def,
        io_manager_key="parquet_io_manager",
        op_tags=k8s_gpu_config,
    )
    def interests(
        context: AssetExecutionContext,
        config: InterestsConfig,
        full_takeout: pl.DataFrame,
    ) -> pl.DataFrame:
        # Enforce the row_limit (if any) per day and sort the data by time because
        # Polars reads data out-of-order
        full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

        sessions_output = get_full_history_sessions(
            full_takeout=full_takeout,
            chunk_size=config.chunk_size,
            first_instruction=spec.first_instruction,
            second_instruction=spec.second_instruction,
            ml_model_name=config.ml_model_name,
        )

        context.add_output_metadata(
            {"count_invalid_responses": sessions_output.count_invalid_responses}
        )

        return sessions_output.output_df

    @asset(
        name=spec.name_prefix + "_interests_embeddings",
        partitions_def=user_partitions_def,
        io_manager_key="parquet_io_manager",
        ins={"interests": AssetIn(key=[spec.name_prefix + "_interests"])},
        op_tags=k8s_gpu_config,
    )
    def interests_embeddings(
        context: AssetExecutionContext,
        config: InterestsEmbeddingsConfig,
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

        context.log.info("Loading the model. This may take a few minutes...")
        model = SentenceTransformer(config.ml_model_name)

        context.log.info("Computing embeddings")
        return df.with_columns(
            embeddings=pl.col("interests").map_batches(
                partial(get_embeddings, model=model),
            )
        )

    @asset(
        name=spec.name_prefix + "_interests_clusters",
        partitions_def=user_partitions_def,
        io_manager_key="parquet_io_manager",
        ins={
            "interests_embeddings": AssetIn(
                key=[spec.name_prefix + "_interests_embeddings"]
            )
        },
        op_tags=k8s_gpu_config,
    )
    def interests_clusters(
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
            cluster_selection_epsilon=0.15,  # 0.15 seems to work well enough
        )
        cluster_labels = clusterer.fit_predict(
            reduced_data_gpu.astype(np.float64).get()
        )

        cluster_stats = np.unique(cluster_labels, return_counts=True)

        context.add_output_metadata(
            {
                "clusters_count": len(cluster_stats[0]),
                "noise_count": int(cluster_stats[1][0])
                if -1 in cluster_stats[0]
                else 0,
            }
        )

        # Remove the embeddings to save space
        return df.with_columns(cluster_label=pl.Series(cluster_labels)).drop(
            "embeddings"
        )

    return [interests, interests_embeddings, interests_clusters]


sensitive_interests_spec = InterestsSpec(
    name_prefix="sensitive",
    first_instruction=(
        "Here is a list of my recent Google search activity. "
        "What have I been doing? What were my goals? "
        "Are there any sensitive psychosocial topics?"
    ),
    second_instruction=(
        "Format the previous answer as a semicolon-separated array of strings delimited by square brackets. "
        "Focus on the goal of the search activity in realtion to the specific topic. "
        "Only include the sensitive psychosocial activity."
    ),
)

general_interests_spec = InterestsSpec(
    name_prefix="general",
    first_instruction=(
        "Here is a list of my recent Google search activity. "
        "What have I been doing? What were my goals?"
    ),
    second_instruction=(
        "Format the previous answer as a semicolon-separated array of strings delimited by square brackets. "
        "Focus on the goal of the search activity in realtion to the specific topic."
    ),
)

interests_assets = [
    # *build_interests_assets(sensitive_interests_spec),
    *build_interests_assets(general_interests_spec),
]
