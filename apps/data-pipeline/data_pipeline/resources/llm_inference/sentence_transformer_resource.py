from typing import TYPE_CHECKING

import polars as pl
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.utils.is_cuda_available import is_cuda_available

if is_cuda_available() or TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = None


class SentenceTransformerResource(ConfigurableResource):
    _model_name = "Salesforce/SFR-Embedding-2_R"
    _model: SentenceTransformer = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        logger = get_dagster_logger()
        logger.info(f"Loading SentenceTransformer model: {self._model_name}")
        self._model = SentenceTransformer(self._model_name)

    def get_embeddings(self, series: pl.Series):
        embeddings = self._model.encode(series.to_list(), precision="float32")
        return pl.Series(
            name="embeddings",
            values=embeddings,
            dtype=pl.Array(
                pl.Float32, self._model.get_sentence_embedding_dimension() or 0
            ),
        )
