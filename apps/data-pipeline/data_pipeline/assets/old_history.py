from functools import partial
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, AssetsDefinition, asset
from pydantic import Field

from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.resources.llm_inference.llama70b_resource import Llama70bResource

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
        llama8b: Llama8bResource,
        full_takeout: pl.DataFrame,
    ) -> pl.DataFrame:
        # Enforce the row_limit (if any) per day and sort the data by time because
        # Polars reads data out-of-order
        full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

        sessions_output = get_full_history_sessions(
            full_takeout=full_takeout,
            chunk_size=config.chunk_size,
            first_instruction=spec.enrichment_prompt_sequence[0],
            second_instruction=spec.enrichment_prompt_sequence[1],
            llama8b=llama8b,
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
            # By specifying an epsilon we can coalesce similar clusters but we rather keep
            # them separate until after the bipartite matching stage
            # cluster_selection_epsilon=0.15,
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

    @asset(
        name=spec.name_prefix + "_cluster_summaries",
        partitions_def=user_partitions_def,
        io_manager_key="parquet_io_manager",
        ins={
            "interests_clusters": AssetIn(
                key=[spec.name_prefix + "_interests_clusters"]
            )
        },
    )
    async def cluster_summaries(
        context: AssetExecutionContext,
        config: RowLimitConfig,
        llama70b: Llama70bResource,
        interests_clusters: pl.DataFrame,
    ) -> pl.DataFrame:
        df = (
            interests_clusters.with_columns(
                (pl.col("date") + pl.lit(":") + pl.col("interests")).alias(
                    "date_interests"
                )
            )
            .group_by("cluster_label")
            .agg([pl.col("date_interests").str.concat("\n").alias("cluster_items")])
            .filter(pl.col("cluster_label") != -1)
        )

        prompt_sequences = [
            [
                f"{spec.clustering_prompt_sequence[0]}\n{row['cluster_items']}",
                spec.clustering_prompt_sequence[1],
            ]
            for row in df.to_dicts()
        ]

        cluster_summaries = await llama70b.get_completions(prompt_sequences)

        return df.with_columns(
            cluster_summary=pl.Series(cluster_summaries),
        ).drop(["cluster_items", "date_interests", "date", "interests"])

    # @asset(
    #     name=spec.name_prefix + "_cluster_summaries",
    #     partitions_def=user_partitions_def,
    #     io_manager_key="parquet_io_manager",
    #     ins={
    #         "cluster_summaries": AssetIn(key=[spec.name_prefix + "_cluster_summaries"])
    #     },
    #     op_tags=k8s_gpu_config,
    # )
    # def summaries_embeddings(
    #     context: AssetExecutionContext,
    #     config: RowLimitConfig,
    #     cluster_summaries: pl.DataFrame,
    # ) -> pl.DataFrame:
    #     return

    return [
        interests,
        interests_embeddings,
        interests_clusters,
        cluster_summaries,
        # summaries_embeddings,
    ]


sensitive_interests_spec = InterestsSpec(
    name_prefix="sensitive",
    enrichment_prompt_sequence=[
        (
            "Here is a list of my recent Google search activity. "
            "What have I been doing? What were my goals? "
            "Are there any sensitive psychosocial topics?"
        ),
        (
            "Format the previous answer as a semicolon-separated array of strings delimited by square brackets. "
            "Focus on the goal of the search activity in realtion to the specific topic. "
            "Only include the sensitive psychosocial activity."
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

interests_assets = [
    *build_interests_assets(general_interests_spec),
    # *build_interests_assets(sensitive_interests_spec),
    # ^ This doesn't seem necessary anymore because llama3 seems good enough
    # at identifying sensitive topics without the specialized prompt
]
