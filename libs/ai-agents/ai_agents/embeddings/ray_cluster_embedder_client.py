import asyncio
import logging
import os
import time
from typing import List, Tuple

import httpx

from .base_embedder_client import BaseEmbedderClient

GPU_BATCH_SIZE = 1  # NB: careful with this one
API_BATCH_SIZE = 2
RUNTIME_COST_HOURLY = (
    0.566 * 4
)  # A100 spot price * nodes (assuming we can get 4 which is not guaranteed)


class RayClusterEmbedderClient(BaseEmbedderClient):
    _timeout: int = 60 * 5
    _max_connections: int = 4
    _max_retries: int = 3

    def __init__(
        self,
        base_url: str,
        max_connections: int | None = None,
        logger: logging.Logger | None = None,
    ):
        super().__init__(logger)
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
        self._remaining_reqs = 0
        self._status_printer_task = None

    async def _periodic_status_printer(self) -> None:
        while True:
            self._logger.info(f"Remaining embedding requests: {self._remaining_reqs}")
            await asyncio.sleep(60)

    async def _get_batch_embeddings(
        self,
        batch: List[str],
        batch_id: int,
        gpu_batch_size: int,
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
                    "normalize_embeddings": True,
                    "batch_size": gpu_batch_size,
                }

                response = await self._client.post(
                    self._base_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                    },
                )
                self._remaining_reqs -= 1
                response.raise_for_status()

                result = response.json()["embeddings"]
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
        api_batch_size: int = API_BATCH_SIZE,
        gpu_batch_size: int = GPU_BATCH_SIZE,
    ) -> Tuple[float, List[List[float]]]:
        self._logger.info(f"Getting embeddings for {len(texts)} texts")

        # Create batches based on max_batch_size
        batches = [
            texts[i : i + api_batch_size] for i in range(0, len(texts), api_batch_size)
        ]

        # Set remaining requests count to number of batches
        self._remaining_reqs = len(batches)
        self._status_printer_task = asyncio.create_task(self._periodic_status_printer())

        t0 = time.time()

        try:
            # If only one batch, run it directly
            if len(batches) == 1:
                responses = [
                    await self._get_batch_embeddings(batches[0], 0, gpu_batch_size)
                ]
            else:
                # If more than one batch, warm up with the first batch
                first_batch_response = await self._get_batch_embeddings(
                    batches[0], 0, gpu_batch_size
                )

                # Then run the remaining batches in parallel
                other_responses = await asyncio.gather(
                    *(
                        self._get_batch_embeddings(batches[i], i, gpu_batch_size)
                        for i in range(1, len(batches))
                    )
                )
                responses = [first_batch_response] + list(other_responses)

            # Combine all embeddings
            all_embeddings = []
            for response in responses:
                all_embeddings.extend(response)

            cost = (time.time() - t0) * RUNTIME_COST_HOURLY / 3600

            return cost, all_embeddings

        finally:
            if self._status_printer_task:
                self._status_printer_task.cancel()

    async def close(self) -> None:
        await self._client.aclose()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    async def test():
        logging.basicConfig(level=logging.INFO)
        client = RayClusterEmbedderClient(
            os.environ["RAY_APP_ADDRESS"],
            logger=logging.getLogger("test"),
        )
        try:
            long_string = (
                "This is a test string that will be repeated multiple times to reach "
                "200+ characters. We need to make sure it's long enough to properly test "
                "the embedding system. This should give us a good sample to work with for "
                "our testing purposes."
            ) * 500
            cost, embeddings = await client.get_embeddings([long_string] * 10_000)
            print(f"Cost: {cost:.2f} USD")
            print(len(embeddings))
        finally:
            await client.close()

    asyncio.run(test())
