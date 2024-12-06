import asyncio
from concurrent.futures import ThreadPoolExecutor

import backoff
import numpy as np
import polars as pl
from dagster import InitResourceContext, get_dagster_logger
from openai import APIError, AsyncOpenAI, RateLimitError
from pydantic import PrivateAttr

from data_pipeline.resources.embeddings.base_embedder_resource import (
    BaseEmbedderResource,
)


class BGEM3Resource(BaseEmbedderResource):
    api_key: str

    _client: AsyncOpenAI = PrivateAttr()
    _cpm: float = 0.01 / 1000

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepinfra.com/v1/openai",
            timeout=60,
        )

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, APIError),
        max_tries=5,
        giveup=lambda e: not (
            isinstance(e, RateLimitError)
            or (
                isinstance(e, APIError)
                and getattr(e, "code", None) == "rate_limit_exceeded"
            )
        ),
    )
    async def _get_batch_embedding(
        self, batch: list[str]
    ) -> tuple[list[list[float]], int]:
        result = await self._client.embeddings.create(
            model="BAAI/bge-m3",
            input=batch,
            encoding_format="float",
        )
        return [data.embedding for data in result.data], result.usage.prompt_tokens

    async def _process_all_batches(
        self, batches: list[list[str]], max_concurrent: int
    ) -> tuple[list[list[float] | None], int]:
        queue = asyncio.Queue()
        total_tokens = 0
        logger = get_dagster_logger()
        tasks_in_progress = 0

        # Add batches with their indices to queue
        for i, batch in enumerate(batches):
            queue.put_nowait((i, batch))

        async def worker():
            nonlocal tasks_in_progress
            worker_results = []
            worker_tokens = 0
            while True:
                try:
                    try:
                        batch_idx, batch = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    tasks_in_progress += 1
                    try:
                        embeddings, tokens = await self._get_batch_embedding(batch)
                        # Store the batch along with its embeddings and index
                        worker_results.append((batch_idx, embeddings, len(batch)))
                        worker_tokens += tokens
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_idx}: {e}")
                        # Store the batch size for failed batches too
                        worker_results.append((batch_idx, None, len(batch)))

                    tasks_in_progress -= 1
                    logger.info(
                        f"Completed batch. Enqueued: {queue.qsize()}, In progress: {tasks_in_progress}"
                    )
                    queue.task_done()
                except Exception as e:
                    tasks_in_progress -= 1
                    logger.error(f"Error in worker: {e}")
                    queue.task_done()
            return worker_results, worker_tokens

        workers = [worker() for _ in range(min(max_concurrent, len(batches)))]
        results = await asyncio.gather(*workers)
        await queue.join()

        # Combine all results
        all_results = []
        for worker_results, tokens in results:
            all_results.extend(worker_results)
            total_tokens += tokens

        # Sort by original batch index and extract embeddings
        all_results.sort(key=lambda x: x[0])
        all_embeddings = []
        for _, emb_batch, batch_size in all_results:
            if emb_batch is None:
                # Use the stored batch_size for failed batches
                all_embeddings.extend([None] * batch_size)
            else:
                all_embeddings.extend(emb_batch)

        return all_embeddings, total_tokens

    def get_embeddings(self, series: pl.Series) -> tuple[pl.Series, float]:
        max_concurrent = 200
        batch_size = 10
        logger = get_dagster_logger()

        truncated_series = series.map_elements(
            lambda text: " ".join(text.split()[:8192])
        )

        # Split into batches of size 10
        batches = [
            truncated_series[i : i + batch_size].to_list()
            for i in range(0, len(truncated_series), batch_size)
        ]

        logger.info(f"Processing {len(batches)} batches of size {batch_size}")

        # Use ThreadPoolExecutor like in remote_llm_resource.py
        def run_async_in_thread(async_func, *args):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_func(*args))
            finally:
                loop.close()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                run_async_in_thread,
                self._process_all_batches,
                batches,
                max_concurrent,
            )
            all_embeddings, total_tokens = future.result()

        # Filter out None values for normalization
        valid_embeddings = [emb for emb in all_embeddings if emb is not None]
        if valid_embeddings:
            embeddings_array = np.array(valid_embeddings)
            normalized = embeddings_array / np.linalg.norm(
                embeddings_array, axis=1, keepdims=True
            )

            # Reconstruct final series with None values in original positions
            final_embeddings = []
            valid_idx = 0
            for emb in all_embeddings:
                if emb is None:
                    final_embeddings.append(None)
                else:
                    final_embeddings.append(normalized[valid_idx].tolist())
                    valid_idx += 1
        else:
            final_embeddings = all_embeddings

        return (
            pl.Series(name="embedding", values=final_embeddings),
            (total_tokens / 1000) * self._cpm,
        )

    async def teardown_after_execution(self, context: InitResourceContext) -> None:
        await self._client.close()
