import asyncio
from logging import Logger
from typing import List, Tuple

from dagster import (
    ConfigurableResource,
    DagsterLogManager,
    InitResourceContext,
    get_dagster_logger,
)
from pydantic import PrivateAttr

from data_pipeline.constants.environments import get_environment
from data_pipeline.utils.embeddings.base_embedder_client import BaseEmbedderClient
from data_pipeline.utils.embeddings.local_embedder_client import LocalEmbedderClient
from data_pipeline.utils.embeddings.ray_cluster_embedder_client import (
    RayClusterEmbedderClient,
)


class BatchEmbedderResource(ConfigurableResource):
    base_url: str

    _client: BaseEmbedderClient = PrivateAttr()
    _logger: DagsterLogManager | Logger = PrivateAttr()
    _loop: asyncio.AbstractEventLoop = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = (
            LocalEmbedderClient()
            if get_environment() == "LOCAL"
            else RayClusterEmbedderClient(
                base_url=self.base_url,
            )
        )
        self._logger = context.log or get_dagster_logger()
        # Initialize the event loop if it doesn't exist
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

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

    def get_embeddings_sync(
        self,
        texts: List[str],
        api_batch_size: int | None = None,
        gpu_batch_size: int | None = None,
    ) -> Tuple[float, List[List[float]]]:
        return self._loop.run_until_complete(
            self.get_embeddings(
                texts=texts,
                api_batch_size=api_batch_size,
                gpu_batch_size=gpu_batch_size,
            )
        )

    async def teardown_after_execution(self, context: InitResourceContext) -> None:
        await self._client.close()
        if self._loop and not self._loop.is_closed():
            self._loop.close()
