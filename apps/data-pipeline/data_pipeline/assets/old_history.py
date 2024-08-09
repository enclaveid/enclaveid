from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.api_db_session import ApiDbSession
from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.resources.llm_inference.llama70b_resource import Llama70bResource
from data_pipeline.resources.llm_inference.sentence_transformer_resource import (
    SentenceTransformerResource,
)
from data_pipeline.utils.database.db_models import (
    BigFive,
    InterestsCluster,
    MoralFoundations,
    UserInterests,
    UserTraits,
)
from data_pipeline.utils.database.postgres import generate_cuid
from data_pipeline.utils.matching.database_interests import insert_cluster_matches
from data_pipeline.utils.matching.database_users import insert_user_matches
from data_pipeline.utils.matching.maximum_bipartite_matching import (
    maximum_bipartite_matching,
)
from data_pipeline.utils.matching.overall_similarity_formula import (
    calculate_big5_similarity,
    calculate_interests_similarity,
    calculate_mft_similarity,
    calculate_overall_similarity,
)

from ..constants.custom_config import RowLimitConfig
from ..constants.k8s import k8s_rapids_config, k8s_vllm_config
from ..partitions import user_partitions_def
from ..utils.capabilities import get_cuda_version, is_rapids_image
from ..utils.old_history_utils import (
    InterestsSpec,
    get_full_history_sessions,
    parse_classification_result,
)

if is_rapids_image() or TYPE_CHECKING:
    import cuml
    import cupy as cp
    from cuml.cluster.hdbscan import HDBSCAN


interests_spec = InterestsSpec(
    enrichment_prompt_sequence=[
        (
            "Here is a list of my recent Google search activity."
            " What have I been doing? What were my goals?"
            " Be as specific as possible, using exact terms from the search activity."
        ),
        (
            "Format the previous answer as a semicolon-separated array of strings delimited by square brackets."
            " Focus on the goal of the search activity in relation to the specific topic."
        ),
    ],
    # The goal of this prompt sequence is classifying the user's search activity
    # similarly to the SEO categories of informational, navigational, and transactional
    summarization_prompt_sequence=[
        lambda search_activity: (
            f"""
Analyze the provided cluster of search activity data for a single topic. Determine whether this cluster primarily represents:

1. A progression in knowledge acquisition and long-term interest, or
2. Reactive searches driven by occasional or recurring needs.

Consider the following factors in your analysis:
- Frequency and regularity of searches
- Diversity of subtopics within the main theme
- Presence of time-bound or event-specific queries
- Indications of recurring but intermittent activities
- Signs of problem-solving for specific occasions rather than general learning

Provide a classification as either 'Knowledge Progression' or 'Reactive Needs', along with a confidence score (0-100%).

Then, offer a brief explanation (2-3 sentences) supporting your classification, highlighting the key factors that influenced your decision.

Format your response as follows:
Classification: [Knowledge Progression/Reactive Needs]
Confidence: [0-100%]
Explanation: [Your 2-3 sentence explanation]

{search_activity}
"""
        ),
        lambda cluster_classification: {
            "unknown": None,
            "reactive": """
Summarize this 'Reactive Needs' search activity cluster in about 100-300 words. Focus on:

- The main category of reactive needs
- Top 3-5 specific types of occasions or needs
- Frequency pattern of these needs
- User's apparent level of experience in addressing these needs
- Any unique elements in the user's approach

Conclude with a single sentence capturing the essence of the user's reactive search behavior.
""",
            "proactive": """
Summarize this 'Knowledge Progression' search activity cluster in about 100-300 words, focusing on the user's learning journey. Describe:

- The main topic or starting point of interest
- 3-5 key areas or subtopics the user explored from this starting point
- How the user's understanding seemed to deepen or branch out in each area
- Any connections or jumps between different areas of exploration
- The most advanced or recent concepts the user has searched for

Conclude with a single sentence capturing the overall trajectory and breadth of the user's learning path.
""",
        }[parse_classification_result(cluster_classification)],
        "Provide a title for the summary. Do not output any additional text other than the title.",
    ],
)


class InterestsConfig(RowLimitConfig):
    ml_model_name: str = Field(
        default="meta-llama/Meta-Llama-3.1-8B-Instruct",
        description=(
            "The Hugging Face model to use as the LLM. See the vLLMs docs for a "
            "list of the support models:\n"
            "https://docs.vllm.ai/en/latest/models/supported_models.html"
        ),
    )

    chunk_size: int = Field(
        default=10,
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
    op_tags=k8s_vllm_config,
)
def interests(
    context: AssetExecutionContext,
    config: InterestsConfig,
    llama8b: Llama8bResource,
    full_takeout: pl.DataFrame,
) -> pl.DataFrame:
    full_takeout = full_takeout.slice(0, config.row_limit).sort("timestamp")

    sessions_output = get_full_history_sessions(
        full_takeout=full_takeout,
        chunk_size=config.chunk_size,
        first_instruction=interests_spec.enrichment_prompt_sequence[0],
        second_instruction=interests_spec.enrichment_prompt_sequence[1],
        llama8b=llama8b,
    )

    context.add_output_metadata(
        {"count_invalid_responses": sessions_output.count_invalid_responses}
    )

    return sessions_output.output_df


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests": AssetIn(key=["interests"])},
    op_tags=k8s_vllm_config,
)
def interests_embeddings(
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
    ins={"interests_embeddings": AssetIn(key=["interests_embeddings"])},
    op_tags=k8s_rapids_config,
)
def interests_clusters(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    interests_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    context.log.info("CUDA version: %s", get_cuda_version())
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


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    op_tags={"dagster/concurrency_key": "llama70b"},
)
async def cluster_summaries(
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
        .agg(
            [
                pl.col("date_interests").str.concat("\n").alias("cluster_items"),
                pl.col("date").sort().alias("cluster_dates"),
            ]
        )
        .filter(pl.col("cluster_label") != -1)
    )

    prompt_sequences = [
        [
            interests_spec.summarization_prompt_sequence[0](row["cluster_items"]),
            interests_spec.summarization_prompt_sequence[1],
            interests_spec.summarization_prompt_sequence[2],
        ]
        for row in df.to_dicts()
    ]

    context.log.info(f"Processing {len(prompt_sequences)} clusters...")
    summaries_completions = await llama70b.get_prompt_sequences_completions(
        prompt_sequences
    )

    cluster_splits = list(
        map(lambda x: x[0] if len(x) > 0 else None, summaries_completions)
    )

    # Tag the clusters with the type of activity: reactive, proactive
    activity_types = []
    for cluster_split in cluster_splits:
        if cluster_split is None:
            activity_types.append("unknown")
        else:
            activity_types.append(parse_classification_result(cluster_split))

    cluster_summaries = list(
        map(lambda x: x[1] if len(x) > 0 else None, summaries_completions)
    )

    cluster_titles = list(
        map(lambda x: x[2] if len(x) > 0 else None, summaries_completions)
    )
    return (
        df.with_columns(
            cluster_dates=df["cluster_dates"],
            cluster_title=pl.Series(cluster_titles),
            cluster_summary=pl.Series(cluster_summaries),
            activity_type=pl.Series(activity_types),
        )
        .filter(pl.col("activity_type") != "unknown")
        .drop(["cluster_items", "date_interests", "date", "interests"])
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"cluster_summaries": AssetIn(key=["cluster_summaries"])},
    op_tags=k8s_vllm_config,
)
def summaries_embeddings(
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
    deps=[summaries_embeddings],
    io_manager_key="parquet_io_manager",
    op_tags=k8s_rapids_config,
)
def summaries_user_matches(
    context: AssetExecutionContext,
    config: RowLimitConfig,
) -> pl.DataFrame:
    current_user_df = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET
        / "summaries_embeddings"
        / f"{context.partition_key}.snappy"
    ).sort(by="cluster_label")

    result_df = pl.DataFrame(
        {
            "user_cluster_label": pl.Series([], dtype=pl.Int32),
            "other_user_cluster_label": pl.Series([], dtype=pl.Int32),
            "cosine_similarity": pl.Series([], dtype=pl.Float64),
            "other_user_id": pl.Series([], dtype=pl.Utf8),
            "activity_type": pl.Series([], dtype=pl.Utf8),
        }
    )

    # Get a list of ready partitions in the parent asset
    other_user_ids = context.instance.get_materialized_partitions(
        context.asset_key_for_input("summaries_embeddings")
    )

    context.log.info(f"Matching with {len(other_user_ids)-1} users")

    # TODO Optimization: Do not recompute the embeddings for the same pair of users
    for other_user_id in other_user_ids:
        if other_user_id == context.partition_key:
            continue

        other_user_df = pl.read_parquet(
            DAGSTER_STORAGE_BUCKET / "summaries_embeddings" / f"{other_user_id}.snappy"
        ).sort(by="cluster_label")

        for activity_type in ["proactive", "reactive"]:
            current_user_activity_df = current_user_df.filter(
                pl.col("activity_type") == activity_type
            )
            other_user_activity_df = other_user_df.filter(
                pl.col("activity_type") == activity_type
            )

            if (
                not current_user_activity_df.is_empty()
                and not other_user_activity_df.is_empty()
            ):
                # Perform the bipartite matching for each user
                match_df = maximum_bipartite_matching(
                    current_user_activity_df["embeddings"].to_numpy(),
                    other_user_activity_df["embeddings"].to_numpy(),
                    current_user_activity_df["cluster_label"].to_numpy(),
                    other_user_activity_df["cluster_label"].to_numpy(),
                )

                # Add the other_user_id to the match_df
                match_df = match_df.with_columns(
                    other_user_id=pl.Series([other_user_id] * len(match_df)),
                    activity_type=pl.Series([activity_type] * len(match_df)),
                )

                result_df = result_df.vstack(match_df)

    return result_df.sort(by="cosine_similarity", descending=True)


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "summaries_user_matches": AssetIn(key=["summaries_user_matches"]),
        "cluster_summaries": AssetIn(key=["cluster_summaries"]),
    },
)
def api_user_matches(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    api_db: ApiDbSession,
    summaries_user_matches: pl.DataFrame,
    cluster_summaries: pl.DataFrame,
) -> None:
    db_conn = api_db.get_session()
    with db_conn.begin():
        user_interests_record_id = db_conn.execute(
            pg_insert(UserInterests)
            .values(
                id=generate_cuid(),
                userId=context.partition_key,
                updatedAt=func.now(),
            )
            .on_conflict_do_update(
                index_elements=[
                    UserInterests.userId,
                ],
                set_={
                    "id": UserInterests.id,
                },
            )
            .returning(UserInterests.id)
        ).fetchone()

        if user_interests_record_id is None:
            raise Exception(
                f"UserInterests record for {context.partition_key} could not be created"
            )

        # Insert clusters with summaries into the database
        current_user_interests_clusters = db_conn.execute(
            pg_insert(InterestsCluster)
            .values(
                cluster_summaries.rename(
                    {
                        "cluster_label": "pipelineClusterId",
                        "activity_type": "clusterType",
                        "cluster_summary": "summary",
                        "cluster_title": "title",
                        "cluster_dates": "activityDates",
                    }
                )
                .with_columns(
                    userInterestsId=pl.Series(
                        [user_interests_record_id[0]] * len(cluster_summaries)
                    ),
                    id=pl.Series(
                        [generate_cuid() for _ in range(len(cluster_summaries))]
                    ),
                    updatedAt=pl.Series([func.now()] * len(cluster_summaries)),
                )
                .to_dicts()
            )
            .on_conflict_do_update(
                index_elements=[
                    InterestsCluster.userInterestsId,
                    InterestsCluster.pipelineClusterId,
                    InterestsCluster.clusterType,
                ],
                set_={
                    "id": InterestsCluster.id,
                },
            )
            .returning(InterestsCluster)
        ).fetchall()

        # Get the InterestsCluster for the other users that we need to match with
        # including the UserInterests
        other_user_interests_clusters = (
            db_conn.query(InterestsCluster, UserInterests)
            .filter(
                or_(
                    *[
                        (UserInterests.userId == other_user_id)
                        & (
                            InterestsCluster.pipelineClusterId
                            == other_user_cluster_label
                        )
                        for other_user_id, other_user_cluster_label in summaries_user_matches[
                            ["other_user_id", "other_user_cluster_label"]
                        ]
                        .unique()
                        .to_numpy()
                    ]
                )
            )
            .filter(UserInterests.id == InterestsCluster.userInterestsId)
            .all()
        )

        insert_cluster_matches(
            current_user_interests_clusters,
            other_user_interests_clusters,
            summaries_user_matches,
            db_conn,
        )

        # Calculate the overall similarities
        current_user_traits = (
            db_conn.query(UserTraits, MoralFoundations, BigFive)
            .join(MoralFoundations, UserTraits.id == MoralFoundations.userTraitsId)
            .join(BigFive, UserTraits.id == BigFive.userTraitsId)
            .filter(UserTraits.userId == context.partition_key)
            .first()
        )

        if current_user_traits:
            other_users_traits = (
                db_conn.query(UserTraits, MoralFoundations, BigFive)
                .filter(
                    UserTraits.userId.in_(
                        [
                            user_interests_record.userId
                            for _, user_interests_record in other_user_interests_clusters
                        ]
                    )
                )
                .filter(UserTraits.id == MoralFoundations.userTraitsId)
                .filter(UserTraits.id == BigFive.userTraitsId)
                .all()
            )

            user_matches_to_insert = []
            _, current_user_mft, current_user_big5 = current_user_traits

            interests_similarities = summaries_user_matches.groupby(
                ["other_user_id", "activity_type"]
            ).agg([pl.col("cosine_similarity").apply(calculate_interests_similarity)])

            for other_user_t, other_user_mft, other_user_big5 in other_users_traits:
                mft_similarity = calculate_mft_similarity(
                    current_user_mft, other_user_mft
                )
                big5_similarity = calculate_big5_similarity(
                    current_user_big5, other_user_big5
                )
                proactive_interests_similarity = interests_similarities.filter(
                    (pl.col("other_user_id") == other_user_t.userId)
                    & (pl.col("activity_type") == "proactive")
                )["cosine_similarity"][0]

                reactive_interests_similarity = interests_similarities.filter(
                    (pl.col("other_user_id") == other_user_t.userId)
                    & (pl.col("activity_type") == "reactive")
                )["cosine_similarity"][0]

                overall_similarity = calculate_overall_similarity(
                    big5_similarity,
                    mft_similarity,
                    proactive_interests_similarity,
                    reactive_interests_similarity,
                )

                user_matches_to_insert.append(
                    {
                        "id": generate_cuid(),
                        "currentUserId": context.partition_key,
                        "otherUserId": other_user_t.userId,
                        "overallSimilarity": overall_similarity,
                        "updatedAt": func.now(),
                    }
                )

            if user_matches_to_insert:
                insert_user_matches(db_conn, user_matches_to_insert)

        db_conn.commit()
