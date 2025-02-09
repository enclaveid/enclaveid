import numpy as np
import polars as pl
from sklearn.decomposition import PCA

PGVECTOR_MAX_DIMENSIONS = 2000


def pad_vectors(vectors: np.ndarray, target_dim: int) -> np.ndarray:
    if vectors.shape[1] >= target_dim:
        return vectors[:, :target_dim]
    padding_width = ((0, 0), (0, target_dim - vectors.shape[1]))
    return np.pad(vectors, padding_width, mode="constant", constant_values=0)


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

    # Pad the reduced embeddings to make it easier to save to DB
    padded_embeddings = pad_vectors(reduced_embeddings, PGVECTOR_MAX_DIMENSIONS)

    # Add padded reduced embeddings back to dataframe
    return df.with_columns(
        pl.Series(output_column_name, padded_embeddings.tolist())
    ), reducer
