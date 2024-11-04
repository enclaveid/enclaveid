import asyncio

import numpy as np
import polars as pl
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from openai import AsyncOpenAI
from pydantic import PrivateAttr


class BGEM3Resource(ConfigurableResource):
    api_key: str

    _client: AsyncOpenAI = PrivateAttr()
    _cpm: float = 0.01 / 1000

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepinfra.com/v1/openai",
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

    def get_embeddings(self, series: pl.Series) -> tuple[pl.Series, float]:
        max_concurrent = 200
        batch_size = len(series) // max_concurrent
        logger = get_dagster_logger()

        # Split into batches
        batches = [
            series[i : i + batch_size].to_list()
            for i in range(0, len(series), batch_size)
        ]

        logger.info(f"Processing {len(batches)} batches of size {batch_size}")

        async def process_all_batches():
            all_embeddings = []
            total_tokens = 0

            # Process batches in chunks of max_concurrent
            for i in range(0, len(batches), max_concurrent):
                batch_chunk = batches[i : i + max_concurrent]
                tasks = [self._get_batch_embedding(batch) for batch in batch_chunk]

                results = await asyncio.gather(*tasks)

                for j, (batch_embeddings, tokens) in enumerate(results):
                    logger.info(f"Completed batch {i + j} of {len(batches)}")
                    all_embeddings.extend(batch_embeddings)
                    total_tokens += tokens

            return all_embeddings, total_tokens

        # Run async code in sync context
        all_embeddings, total_tokens = asyncio.run(process_all_batches())

        # Normalize all embeddings together
        embeddings = np.array(all_embeddings)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        return (
            pl.Series(name="embedding", values=embeddings),
            (total_tokens / 1000) * self._cpm,
        )

    async def teardown_after_execution(self, context: InitResourceContext) -> None:
        await self._client.close()
