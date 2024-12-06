import time

import polars as pl
from dagster import InitResourceContext, get_dagster_logger
from openai import OpenAI
from pydantic import PrivateAttr

from data_pipeline.resources.embeddings.base_embedder_resource import (
    BaseEmbedderResource,
)


class NVEmbedServerlessResource(BaseEmbedderResource):
    _model_name = "nvidia/nv-embedqa-mistral-7b-v2"
    _client: OpenAI = PrivateAttr()
    _time_start: float = PrivateAttr()

    api_key: str

    def setup_for_execution(self, context: InitResourceContext | None = None) -> None:
        logger = get_dagster_logger()
        logger.info(f"Initializing NVIDIA API client for model: {self._model_name}")
        self._time_start = time.time()

        self._client = OpenAI(
            api_key=self.api_key,
            base_url="https://integrate.api.nvidia.com/v1",
        )

        logger.info(
            f"Client initialized in {(time.time() - self._time_start):.2f} seconds"
        )

    def get_embeddings(self, series: pl.Series) -> tuple[pl.Series, float]:
        texts = series.to_list()
        embeddings = []

        response = self._client.embeddings.create(
            input=texts,
            model=self._model_name,
            encoding_format="float",
            extra_body={"input_type": "passage", "truncate": "NONE"},
        )

        embeddings = [data.embedding for data in response.data]

        # TODO: Implement cost calculation
        cost = 0.0

        return (
            pl.Series(
                name="embeddings",
                values=embeddings,
                dtype=pl.Array(pl.Float32, len(embeddings[0]) if embeddings else 0),
            ),
            cost,
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # No cleanup needed for API client
        pass
