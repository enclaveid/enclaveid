import asyncio
import logging
import os
import time
from typing import List, Tuple

import httpx
import numpy as np

from .base_embedder_client import BaseEmbedderClient

DEFAULT_MAX_BATCH_SIZE = (
    200  # Over a certain size, the API starts to send async responses (wtf)
)


class RunpodEmbedderClient(BaseEmbedderClient):
    _timeout: int = 60 * 10
    _n_workers: int = 3
    _max_connections: int = (
        30  # Keep this low enough to avoid more than 60s in the queue
    )
    _cps: float = 0.00076 * _n_workers
    _max_retries: int = 3
    _poll_interval: int = 30  # seconds between polling for job status
    _max_poll_attempts: int = 60  # max attempts to poll for job completion

    def __init__(
        self,
        api_key: str,
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
        )
        self._api_key = api_key
        self._base_url = base_url
        self._remaining_reqs = 0
        self._status_printer_task = None

    async def _periodic_status_printer(self) -> None:
        while True:
            self._logger.info(f"Remaining embedding requests: {self._remaining_reqs}")
            await asyncio.sleep(60)

    async def _poll_job_status(self, job_id: str) -> dict | None:
        """Poll the job status endpoint until the job is completed or fails."""
        status_url = self._base_url.replace("/run", "/status") + f"/{job_id}"

        for attempt in range(self._max_poll_attempts):
            try:
                response = await self._client.get(
                    status_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                        "api-key": self._api_key,
                    },
                )
                response.raise_for_status()
                result = response.json()
                status = result.get("status")

                if status == "COMPLETED":
                    return result
                elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
                    # Terminal failure states
                    self._logger.error(f"Job {job_id} ended in status: {status}")
                    return None

                # If not completed or failed, wait and try again
                await asyncio.sleep(self._poll_interval)

            except Exception as e:
                self._logger.error(f"Error polling status for job {job_id}: {e}")
                await asyncio.sleep(self._poll_interval)

        self._logger.error(f"Max polling attempts reached for job {job_id}")
        return None

    def _extract_and_normalize_embeddings(self, data: List[dict]) -> List[List[float]]:
        embeddings = np.array([d["embedding"] for d in data])
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings.tolist()

    async def _process_response(
        self, response: httpx.Response, batch_id: int
    ) -> List[List[float]] | None:
        """Process the initial response from the run endpoint. If it's a job record or
        if it is COMPLETED with no output, poll until done."""
        try:
            result = response.json()
        except Exception as e:
            self._logger.error(
                f"Could not parse JSON response for batch {batch_id}: {e}"
            )
            return None

        # If we got a job record without output, we must poll for completion
        if "id" in result and "status" in result and "output" not in result:
            job_id = result["id"]
            status = result["status"]

            # If the job is completed but we have no output, we still need to poll status
            if status == "COMPLETED":
                self._logger.info(
                    f"Job {job_id} is COMPLETED but has no output. Polling status."
                )
            else:
                self._logger.info(f"Job {job_id} not completed yet, polling status.")

            polled_result = await self._poll_job_status(job_id)
            if polled_result is None:
                # Job failed or never completed
                return None

            self._logger.info(f"Polled job {job_id}: {polled_result}")
            # After polling, we should have output
            if "output" not in polled_result or "data" not in polled_result["output"]:
                self._logger.error(f"Completed job {job_id} has no output data.")
                return None
            return self._extract_and_normalize_embeddings(
                polled_result["output"]["data"]
            )

        # Otherwise, we assume we got a direct result with embeddings
        if not result.get("output", {}).get("data"):
            self._logger.error(f"Empty result received for batch {batch_id}: {result}")
            return None  # Caller will handle retry logic

        # Extract embeddings directly
        return self._extract_and_normalize_embeddings(result["output"]["data"])

    async def get_embeddings(
        self, texts: List[str], batch_size: int = DEFAULT_MAX_BATCH_SIZE
    ) -> Tuple[float, List[List[float]]]:
        self._logger.info(f"Getting embeddings for {len(texts)} texts")

        time_start = time.time()
        # Add </s> token to each text
        texts = [text + " </s>" for text in texts]

        # Create batches based on max_batch_size
        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

        # Set remaining requests count to number of batches instead of texts
        self._remaining_reqs = len(batches)
        self._status_printer_task = asyncio.create_task(self._periodic_status_printer())

        try:

            async def get_batch_embeddings(
                batch: List[str], batch_id: int
            ) -> List[List[float] | None]:
                result_embeddings = None
                response = None

                for attempt in range(self._max_retries):
                    try:
                        payload = {
                            "input": {
                                "model": "nvidia/NV-Embed-v2",
                                "input": batch,
                            }
                        }

                        response = await self._client.post(
                            self._base_url,
                            json=payload,
                            headers={
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {self._api_key}",
                                "api-key": self._api_key,
                            },
                        )
                        self._remaining_reqs -= 1
                        response.raise_for_status()

                        result_embeddings = await self._process_response(
                            response, batch_id
                        )
                        if result_embeddings is None:
                            # This indicates either empty result or failed job scenario, so retry
                            if attempt < self._max_retries - 1:
                                self._logger.info(
                                    f"Retrying batch {batch_id} (attempt {attempt + 2}/{self._max_retries})"
                                )
                                continue
                            else:
                                # Max attempts reached
                                return [None] * len(batch)
                        # If we got a valid embeddings list
                        return [embedding for embedding in result_embeddings]

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

                # Should never reach here because of return statements
                return [None] * len(batch)

            # Run requests concurrently
            responses = await asyncio.gather(
                *(get_batch_embeddings(batch, i) for i, batch in enumerate(batches))
            )

            # Combine all embeddings
            all_embeddings = []
            for response in responses:
                all_embeddings.extend(response)

            time_end = time.time()
            cost = (time_end - time_start) * self._cps

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
        client = RunpodEmbedderClient(
            os.environ["RUNPOD_API_KEY"],
            "https://api.runpod.ai/v2/g7i48jcm62o1q2/run",
            logger=logging.getLogger("test"),
        )
        try:
            long_string = (
                "This is a test string that will be repeated multiple times to reach "
                "200+ characters. We need to make sure it's long enough to properly test "
                "the embedding system. This should give us a good sample to work with for "
                "our testing purposes."
            ) * 100
            cost, embeddings = await client.get_embeddings([long_string] * 100, 1)
            print(f"Cost: {cost:.2f} USD")
            print(len(embeddings))
        finally:
            await client.close()

    asyncio.run(test())
