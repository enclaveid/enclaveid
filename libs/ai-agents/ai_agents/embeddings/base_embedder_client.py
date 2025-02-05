import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseEmbedderClient(ABC):
    """
    Abstract base class for embedder clients.
    """

    _logger: logging.Logger
    _loop: asyncio.AbstractEventLoop

    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger(__name__)
        # Initialize the event loop if it doesn't exist
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def get_embeddings_sync(
        self, texts: List[str], gpu_batch_size: int = 1, api_batch_size: int = 1
    ):
        return self._loop.run_until_complete(
            self.get_embeddings(texts, gpu_batch_size, api_batch_size)
        )

    @abstractmethod
    async def get_embeddings(
        self, texts: List[str], gpu_batch_size: int = 1, api_batch_size: int = 1
    ) -> Tuple[float, List[List[float]]]:
        """Get embeddings for a list of texts."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any resources used by the embedder."""
        pass
