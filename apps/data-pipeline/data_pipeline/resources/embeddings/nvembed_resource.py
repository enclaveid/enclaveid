import time
from typing import TYPE_CHECKING, Any, Dict, Literal

import polars as pl
from dagster import InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.resources.embeddings.base_embedder_resource import (
    BaseEmbedderResource,
)
from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.costs import get_gpu_runtime_cost

if is_vllm_image() or TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = None


class NVEmbedResource(BaseEmbedderResource):
    _model_name = "nvidia/NV-Embed-v2"
    _model: SentenceTransformer = PrivateAttr()
    _pool: Dict[Literal["input", "output", "processes"], Any] | None = PrivateAttr()
    _time_start: float = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext | None = None) -> None:
        logger = get_dagster_logger()
        logger.info(f"Loading SentenceTransformer model: {self._model_name}")
        self._time_start = time.time()

        model = SentenceTransformer(self._model_name, trust_remote_code=True)
        model.max_seq_length = 32768
        model.tokenizer.padding_side = "right"
        self._model = model

        gpu_count = len(gpu_info(return_list=True))
        if gpu_count > 1:
            logger.info(f"Using multi-process pool with {gpu_count} GPUs")
            self._pool = self._model.start_multi_process_pool()
        else:
            logger.info("Using single GPU mode")
            self._pool = None

        logger.info(f"Model loaded in {(time.time() - self._time_start):.2f} seconds")

    def get_embeddings(self, series: pl.Series) -> tuple[pl.Series, float]:
        if self._pool is not None:
            embeddings = self._model.encode_multi_process(
                self._add_eos(series.to_list()),
                self._pool,
                batch_size=2,
                normalize_embeddings=True,
            )
        else:
            embeddings = self._model.encode(
                self._add_eos(series.to_list()),
                batch_size=2,
                normalize_embeddings=True,
                show_progress_bar=True,
            )

        cost = get_gpu_runtime_cost(self._time_start)

        return (
            pl.Series(
                name="embeddings",
                values=embeddings,
                dtype=pl.Array(
                    pl.Float32, self._model.get_sentence_embedding_dimension() or 0
                ),
            ),
            cost,
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        if self._pool is not None:
            self._model.stop_multi_process_pool(self._pool)
