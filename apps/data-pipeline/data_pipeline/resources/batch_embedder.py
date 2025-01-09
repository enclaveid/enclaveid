from logging import Logger
from typing import List, Tuple

from dagster import (
    ConfigurableResource,
    DagsterLogManager,
    InitResourceContext,
    get_dagster_logger,
)
from pydantic import PrivateAttr

from data_pipeline.utils.ray_cluster_embedder_client import RayClusterEmbedderClient


class BatchEmbedderResource(ConfigurableResource):
    base_url: str

    _client: RayClusterEmbedderClient = PrivateAttr()
    _logger: DagsterLogManager | Logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = RayClusterEmbedderClient(
            base_url=self.base_url,
        )
        self._logger = context.log or get_dagster_logger()

    async def get_embeddings(
        self,
        texts: List[str],
        api_batch_size: int | None = None,
        gpu_batch_size: int | None = None,
    ) -> Tuple[float, List[List[float]]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: The texts to embed
            api_batch_size: The batch size for the API. At each given time, the API will process this many texts x4 (for each of the 4 GPUs).
            gpu_batch_size: The batch size for the GPU. Adjust this based on the length of the input texts to avoid OOM errors.

        Returns:
            The cost of the embeddings and the embeddings
        """
        try:
            kwargs = {}
            if gpu_batch_size is not None:
                kwargs["gpu_batch_size"] = gpu_batch_size
                # The API batch size should be at least as large as the GPU batch size
                kwargs["api_batch_size"] = gpu_batch_size

            if api_batch_size is not None:
                kwargs["api_batch_size"] = api_batch_size

            return await self._client.get_embeddings(texts, **kwargs)
        except Exception as e:
            self._logger.error(f"Error getting embeddings: {e}")
            await self._client.close()
            raise e

    async def teardown_after_execution(self, context: InitResourceContext) -> None:
        await self._client.close()
