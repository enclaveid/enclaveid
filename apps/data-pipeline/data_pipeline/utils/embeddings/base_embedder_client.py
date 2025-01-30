from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseEmbedderClient(ABC):
    """
    Abstract base class for embedder clients.
    """

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
