import asyncio
from typing import List, Tuple

from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient
from ai_agents.embeddings.deepinfra_embedder_client import DeepInfraEmbedderClient
from dagster import (
    ConfigurableResource,
    InitResourceContext,
    get_dagster_logger,
)
from pydantic import PrivateAttr


class BatchEmbedderResource(ConfigurableResource, BaseEmbedderClient):
    api_key: str | None = None
    base_url: str | None = None

    _client: BaseEmbedderClient = PrivateAttr()
    _loop: asyncio.AbstractEventLoop = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = (
            DeepInfraEmbedderClient(api_key=self.api_key, logger=get_dagster_logger())
            # LocalEmbedderClient()
            # if get_environment() == "LOCAL"
            # else RayClusterEmbedderClient(
            #     base_url=self.base_url, logger=get_dagster_logger()
            # )
        )
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
            await self._client.close()
            raise e

    async def close(self) -> None:
        await self._client.close()

    async def teardown_after_execution(self, context: InitResourceContext) -> None:
        await self.close()
