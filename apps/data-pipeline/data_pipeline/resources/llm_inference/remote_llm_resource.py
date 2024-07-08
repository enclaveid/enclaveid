import asyncio
from typing import Any, Dict, List

import httpx
from dagster import ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr


class RemoteLlmResource(ConfigurableResource):
    api_key: str

    _concurrency_limit: int = PrivateAttr()
    _timeout: int = PrivateAttr()
    _inference_url: str = PrivateAttr()
    _inference_config: Dict[str, Any] = PrivateAttr()

    _client: httpx.AsyncClient = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=self._concurrency_limit,
                max_keepalive_connections=self._concurrency_limit,
            ),
            timeout=self._timeout,
        )

    async def _get_completion(
        self,
        conversation: List[Dict[str, str]],
    ) -> str:
        response = await self._client.post(
            self._inference_url,
            json={
                "messages": conversation,
                **self._inference_config,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        response.raise_for_status()
        res = response.json()
        return res["choices"][0]["message"]["content"]

    async def _get_prompt_sequence_completion(
        self,
        prompts_sequence: List[str],
    ):
        conversation: List[Dict[str, str]] = []

        for prompt in prompts_sequence:
            conversation.append({"role": "user", "content": prompt})
            response = await self._get_completion(conversation)
            conversation.append({"role": "assistant", "content": response})
        return conversation

    async def get_prompt_sequences_completions(self, prompt_sequences: List[List[str]]):
        conversations = await asyncio.gather(
            *(
                self._get_prompt_sequence_completion(prompt_sequence)
                for prompt_sequence in prompt_sequences
            )
        )

        # Only return the final assistant's response
        return list(map(lambda x: x[-1]["content"], conversations))
