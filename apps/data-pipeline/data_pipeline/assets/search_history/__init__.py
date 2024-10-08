from data_pipeline.assets.search_history.aspects_embeddings import (
    aspects_embeddings,
)
from data_pipeline.assets.search_history.aspects_matches import aspects_matches
from data_pipeline.assets.search_history.cluster_summaries import cluster_summaries
from data_pipeline.assets.search_history.clusters_categories import clusters_categories
from data_pipeline.assets.search_history.funny_cluster_summaries import (
    funny_cluster_summaries,
)
from data_pipeline.assets.search_history.funny_images import funny_images
from data_pipeline.assets.search_history.interests import interests
from data_pipeline.assets.search_history.interests_clusters import interests_clusters
from data_pipeline.assets.search_history.interests_embeddings import (
    interests_embeddings,
)
from data_pipeline.assets.search_history.results_for_api import results_for_api
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
    interests_clusters,
    clusters_categories,
    cluster_summaries,
    funny_cluster_summaries,
    funny_images,
    aspects_embeddings,
    aspects_matches,
    summaries_user_matches,
    summaries_interests_matches,
    summaries_user_matches_with_desc,
    results_for_api,
]
