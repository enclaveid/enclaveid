import asyncio
import logging
from typing import List, Tuple

import httpx

from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient


class DeepInfraEmbedderClient(BaseEmbedderClient):
    """
    A client for obtaining embeddings from the deepinfra API.
    """

    _api_key: str

    _cost_per_token = 0.0100 / 1_000_000

    _timeout: int = 60
    _max_connections: int = 50
    _max_retries: int = 3
    _last_log_time: float = 0
    _completed_requests: int = 0

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepinfra.com/v1/inference/BAAI/bge-en-icl",
        max_connections: int | None = None,
        logger: logging.Logger | None = None,
    ):
        super().__init__(logger or logging.getLogger(__name__))

        self._max_connections = max_connections or self._max_connections

        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            limits=httpx.Limits(
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_connections,
            ),
            verify=False,
        )
        self._base_url = base_url
        self._api_key = api_key
        self._status_printer_task = None
        self._total_tokens = 0

    async def _periodic_status_printer(self, total_texts: int) -> None:
        start_time = asyncio.get_event_loop().time()
        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - self._last_log_time >= 60:  # Only log every 60 seconds
                progress = (self._completed_requests) / total_texts
                elapsed_time = current_time - start_time
                estimated_total_time = elapsed_time / progress if progress > 0 else 0
                estimated_remaining_time = estimated_total_time - elapsed_time

                self._logger.info(
                    f"Progress: {progress:.1%} | "
                    f"Elapsed: {elapsed_time:.1f}s | "
                    f"Estimated remaining: {estimated_remaining_time:.1f}s"
                )
                self._last_log_time = current_time
            await asyncio.sleep(60)

    async def _get_batch_embeddings(
        self,
        batch: List[str],
        batch_id: int,
    ) -> List[List[float] | None]:
        """
        A helper function that sends a single batch request to the server
        and handles retries.
        """
        response = None

        for attempt in range(self._max_retries):
            try:
                payload = {
                    "inputs": batch,
                    "normalize": True,
                }

                response = await self._client.post(
                    self._base_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                )
                self._completed_requests += 1
                response.raise_for_status()

                json_response = response.json()

                self._total_tokens += json_response["input_tokens"]

                result = json_response["embeddings"]
                return result

            except Exception as e:
                error_details = response.text if response else str(e)

                self._logger.error(
                    f"Error processing batch {batch_id} of size {len(batch)}: {error_details}"
                )
                if attempt < self._max_retries - 1:
                    self._logger.info(
                        f"Retrying batch {batch_id} (attempt {attempt + 2}/{self._max_retries})"
                    )
                    continue

                # Max attempts reached
                return [None] * len(batch)

        # Should never reach here because of the return statements
        return [None] * len(batch)

    async def get_embeddings(
        self,
        texts: List[str],
        api_batch_size: int = 100,
        gpu_batch_size: int = 0,
    ) -> Tuple[float, List[List[float]]]:
        self._logger.info(f"Getting embeddings for {len(texts)} texts")

        # Create batches based on max_batch_size
        batches = [
            texts[i : i + api_batch_size] for i in range(0, len(texts), api_batch_size)
        ]

        self._status_printer_task = asyncio.create_task(
            self._periodic_status_printer(len(texts))
        )

        try:
            # If only one batch, run it directly
            if len(batches) == 1:
                responses = [await self._get_batch_embeddings(batches[0], 0)]
            else:
                # If more than one batch, warm up with the first batch
                first_batch_response = await self._get_batch_embeddings(batches[0], 0)

                # Then run the remaining batches in parallel
                other_responses = await asyncio.gather(
                    *(
                        self._get_batch_embeddings(batches[i], i)
                        for i in range(1, len(batches))
                    )
                )
                responses = [first_batch_response] + list(other_responses)

            # Combine all embeddings
            all_embeddings = []
            for response in responses:
                all_embeddings.extend(response)

            cost = self._total_tokens * self._cost_per_token

            return cost, all_embeddings

        finally:
            if self._status_printer_task:
                self._status_printer_task.cancel()

    async def close(self) -> None:
        await self._client.aclose()


if __name__ == "__main__":
    import os

    async def main():
        client = DeepInfraEmbedderClient(api_key=os.environ["DEEPINFRA_API_KEY"])
        cost, embeddings = await client.get_embeddings(["Hello, world!"] * 100 * 200)
        print(cost)
        print(len(embeddings))
        await client.close()

    asyncio.run(main())
