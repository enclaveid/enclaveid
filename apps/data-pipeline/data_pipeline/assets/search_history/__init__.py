from data_pipeline.assets.search_history.cluster_summaries import cluster_summaries
from data_pipeline.assets.search_history.dissimilar_funny_interests import (
    dissimilar_funny_interests,
)
from data_pipeline.assets.search_history.dissimilar_interests_clusters import (
    dissimilar_interests_clusters,
)
from data_pipeline.assets.search_history.funny_cluster_summaries import (
    funny_cluster_summaries,
)
from data_pipeline.assets.search_history.interests import interests
from data_pipeline.assets.search_history.interests_clusters import interests_clusters
from data_pipeline.assets.search_history.interests_embeddings import (
    interests_embeddings,
)
from data_pipeline.assets.search_history.results_for_api import results_for_api
from data_pipeline.assets.search_history.summaries_embeddings import (
    summaries_embeddings,
)
from data_pipeline.assets.search_history.summaries_interests_matches import (
    summaries_interests_matches,
)
from data_pipeline.assets.search_history.summaries_user_matches import (
    summaries_user_matches,
)
from data_pipeline.assets.search_history.summaries_user_matches_with_desc import (
    summaries_user_matches_with_desc,
)

__all__ = [
    interests,
    interests_embeddings,
    dissimilar_funny_interests,
    interests_clusters,
    dissimilar_interests_clusters,
    cluster_summaries,
    funny_cluster_summaries,
    summaries_embeddings,
    summaries_user_matches,
    summaries_interests_matches,
    summaries_user_matches_with_desc,
    results_for_api,
]
