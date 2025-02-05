import asyncio
import logging
from typing import List, Tuple

import numpy as np
from openai import AsyncOpenAI

from .base_embedder_client import BaseEmbedderClient


class DeepInfraEmbedderClient(BaseEmbedderClient):
    """
    A client for obtaining embeddings from the deepinfra API.
    """

    _cost_per_second = 0.0005

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        logger: logging.Logger | None = None,
    ):
        super().__init__(logger)
        # Create an OpenAI client with your deepinfra token and endpoint
        self.openai = AsyncOpenAI(
            api_key=api_key, base_url=base_url or "https://api.deepinfra.com/v1/openai"
        )

    async def get_embeddings(
        self, texts: List[str], gpu_batch_size: int = 1, api_batch_size: int = 100
    ) -> Tuple[float, List[List[float]]]:
        """
        Get embeddings for a list of texts using the deepinfra API.

        Parameters:
            texts (List[str]): The list of texts to embed.
            gpu_batch_size (int): Not used in this implementation.
            api_batch_size (int): Maximum number of texts to process in a single API call.

        Returns:
            Tuple[float, List[List[float]]]:
                A tuple where the first element is the prompt token usage (as a float)
                and the second is a list of embeddings (each a list of floats).
        """
        # Record start time for cost calculation
        start_time = asyncio.get_event_loop().time()
        last_log_time = start_time
        total_cost = 0.0
        all_embeddings = []
        total_texts = len(texts)

        # Process texts in batches
        for i in range(0, total_texts, api_batch_size):
            batch_texts = texts[i : i + api_batch_size]

            # Calculate progress metrics
            current_time = asyncio.get_event_loop().time()
            if current_time - last_log_time >= 60:  # Only log every 60 seconds
                progress = (i + len(batch_texts)) / total_texts
                elapsed_time = current_time - start_time
                estimated_total_time = elapsed_time / progress if progress > 0 else 0
                estimated_remaining_time = estimated_total_time - elapsed_time

                self._logger.info(
                    f"Progress: {progress:.1%} | "
                    f"Elapsed: {elapsed_time:.1f}s | "
                    f"Estimated remaining: {estimated_remaining_time:.1f}s"
                )
                last_log_time = current_time

            # Use the async client for each batch
            result = await self.openai.embeddings.create(
                model="BAAI/bge-en-icl",
                input=batch_texts,
                encoding_format="float",
            )

            # Process the result: extract embeddings
            for item in result.data:
                all_embeddings.append(item.embedding)

        # Calculate total elapsed time and cost
        elapsed_time = asyncio.get_event_loop().time() - start_time
        total_cost = elapsed_time * self._cost_per_second

        # Convert to numpy array and normalize all at once
        embeddings_array = np.array(all_embeddings)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        all_embeddings = (embeddings_array / norms).tolist()

        return total_cost, all_embeddings

    async def close(self) -> None:
        await self.openai.close()


if __name__ == "__main__":
    import os

    async def main():
        client = DeepInfraEmbedderClient(api_key=os.environ["DEEPINFRA_API_KEY"])
        cost, embeddings = await client.get_embeddings(["Hello, world!"] * 100)
        print(cost)
        print(len(embeddings))
        await client.close()

    asyncio.run(main())
