import numpy as np
import polars as pl
from sklearn.decomposition import PCA

PGVECTOR_MAX_DIMENSIONS = 2000


def reduce_df_embeddings(
    df: pl.DataFrame,
    max_components: int = PGVECTOR_MAX_DIMENSIONS,
    input_column_name="embedding",
    output_column_name="reduced_embedding",
) -> tuple[pl.DataFrame, PCA]:
    embeddings = np.stack(df[input_column_name].to_list())

    reducer = PCA(
        n_components=min(max_components, embeddings.shape[0]),
        random_state=42,
        svd_solver="randomized",
    )
    reduced_embeddings = reducer.fit_transform(embeddings)

    # Add reduced embeddings back to dataframe
    return df.with_columns(
        pl.Series(output_column_name, reduced_embeddings.tolist())
    ), reducer
