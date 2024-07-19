import asyncio
from typing import Any, Dict, List

import httpx
from curlify2 import Curlify
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
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
    ) -> str | None:
        payload = {
            "messages": conversation,
            **self._inference_config,
        }
        response = await self._client.post(
            self._inference_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            response.raise_for_status()
            res = response.json()
            return res["choices"][0]["message"]["content"]
        except Exception as e:
            curl = Curlify(response.request)  # type: ignore
            get_dagster_logger().error(
                f"Error in LLM completion: {e}. Request: {curl.to_curl()}"
            )

            return None

    async def _get_prompt_sequence_completion(self, prompts_sequence: List[str]):
        conversation: List[Dict[str, str]] = []

        for prompt in prompts_sequence:
            conversation.append({"role": "user", "content": prompt})
            response = await self._get_completion(conversation)
            if not response:
                return []
            else:
                conversation.append({"role": "assistant", "content": response})

        return conversation

    async def get_prompt_sequences_completions(
        self, prompt_sequences: List[List[str]]
    ) -> List[List[str | None]]:
        conversations = await asyncio.gather(
            *(
                self._get_prompt_sequence_completion(prompt_sequence)
                for prompt_sequence in prompt_sequences
            )
        )

        # Assume all prompt sequences have the same length
        prompt_sequences_length = len(prompt_sequences[0])

        # Return all the assistant responses, only for completed conversations
        return list(
            map(
                lambda x: [message["content"] for message in x[1::2]]
                if len(x) == prompt_sequences_length * 2
                else [],
                conversations,
            )
        )
