from typing import TYPE_CHECKING, Any, Dict, Literal

import polars as pl
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import is_vllm_image

if is_vllm_image() or TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = None


class SentenceTransformerResource(ConfigurableResource):
    _model_name = "Salesforce/SFR-Embedding-2_R"
    _model: SentenceTransformer = PrivateAttr()
    _pool: Dict[Literal["input", "output", "processes"], Any] = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        logger = get_dagster_logger()
        logger.info(f"Loading SentenceTransformer model: {self._model_name}")
        self._model = SentenceTransformer(self._model_name)
        self._pool = self._model.start_multi_process_pool()

    def get_embeddings(self, series: pl.Series):
        embeddings = self._model.encode_multi_process(series.to_list(), self._pool)
        return pl.Series(
            name="embeddings",
            values=embeddings,
            dtype=pl.Array(
                pl.Float32, self._model.get_sentence_embedding_dimension() or 0
            ),
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        self._model.stop_multi_process_pool(self._pool)
