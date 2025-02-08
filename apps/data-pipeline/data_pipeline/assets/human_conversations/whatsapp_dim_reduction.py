import joblib
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field
from sklearn.decomposition import PCA

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.utils.get_working_dir import get_working_dir


class WhatsappDimReductionConfig(Config):
    max_components: int = Field(
        default=2000,
        description="The maximum number of components to reduce the embeddings to.",
    )


@asset(
    ins={
        "whatsapp_node_sentiments": AssetIn(
            key="whatsapp_node_sentiments",
        )
    },
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
)
def whatsapp_dim_reduction(
    context: AssetExecutionContext,
    whatsapp_node_sentiments: pl.DataFrame,
    config: WhatsappDimReductionConfig,
):
    # Convert embeddings to numpy array
    embeddings = np.stack(whatsapp_node_sentiments["embedding"].to_numpy())

    reducer = PCA(
        n_components=min(config.max_components, embeddings.shape[0]),
        random_state=42,
        svd_solver="randomized",
    )
    reduced_embeddings = reducer.fit_transform(embeddings)

    working_dir = get_working_dir(context)
    working_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(reducer, working_dir / f"{context.partition_key}.reducer.joblib")

    # Add reduced embeddings back to dataframe
    return whatsapp_node_sentiments.with_columns(
        pl.Series("reduced_embedding", reduced_embeddings.tolist())
    )
