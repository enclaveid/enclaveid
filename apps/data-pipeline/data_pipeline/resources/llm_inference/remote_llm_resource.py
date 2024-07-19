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
    _retry_event: asyncio.Event = PrivateAttr(default_factory=asyncio.Event)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=self._concurrency_limit,
                max_keepalive_connections=self._concurrency_limit,
            ),
            timeout=self._timeout,
        )
        self._retry_event.set()  # Initially allow all operations

    async def _get_completion(
        self,
        conversation: List[Dict[str, str]],
        conversation_id: int,
    ) -> str | None:
        payload = {
            "messages": conversation,
            **self._inference_config,
        }

        max_attempts = 3  # Define max retry attempts
        logger = get_dagster_logger()

        for _ in range(max_attempts):
            await self._retry_event.wait()  # Wait if currently in retry mode

            response = await self._client.post(
                self._inference_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait_time = int(retry_after)
                    # logger.info(
                    #     f"429 Too Many Requests: Retrying completion #{conversation_id} after {wait_time} seconds."
                    # )
                    self._retry_event.clear()  # Block further requests
                    await asyncio.sleep(wait_time)  # Wait as advised by the server
                    self._retry_event.set()  # Allow requests again
                    continue

            try:
                response.raise_for_status()
                res = response.json()
                return res["choices"][0]["message"]["content"]
            except Exception as e:
                curl = Curlify(response.request)
                logger.error(
                    f"Error in LLM completion #{conversation_id}: {e}. Request: {curl.to_curl()}"
                )
                return None

        logger.error(
            f"Failed to get completion #{conversation_id} after {max_attempts} attempts."
        )
        return None

    async def _get_prompt_sequence_completion(
        self, prompts_sequence: List[str], conversation_id: int
    ) -> List[Dict[str, str]]:
        conversation: List[Dict[str, str]] = []

        for prompt in prompts_sequence:
            conversation.append({"role": "user", "content": prompt})
            response = await self._get_completion(conversation, conversation_id)
            if not response:
                return []
            else:
                conversation.append({"role": "assistant", "content": response})

        return conversation

    async def get_prompt_sequences_completions(
        self, prompt_sequences: List[List[str]]
    ) -> List[List[str]]:
        conversations = await asyncio.gather(
            *(
                self._get_prompt_sequence_completion(prompt_sequence, i)
                for i, prompt_sequence in enumerate(prompt_sequences)
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
