import asyncio
from typing import Any, Callable, Dict, List

import httpx
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

PromptSequence = List[str] | List[Callable[[str], str]]


class RemoteLlmResource(ConfigurableResource):
    api_key: str

    _concurrency_limit: int = PrivateAttr()
    _timeout: int = PrivateAttr()
    _inference_url: str = PrivateAttr()
    _inference_config: Dict[str, Any] = PrivateAttr()
    _input_cpm: float = PrivateAttr()
    _output_cpm: float = PrivateAttr()
    _context_length: int = PrivateAttr()

    _client: httpx.AsyncClient = PrivateAttr()
    _retry_event: asyncio.Event = PrivateAttr(default_factory=asyncio.Event)
    _remaining_reqs: int = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=self._concurrency_limit,
                max_keepalive_connections=self._concurrency_limit,
            ),
            timeout=self._timeout,
        )
        self._retry_event.set()  # Initially allow all operations

    async def _periodic_status_printer(self) -> None:
        logger = get_dagster_logger()
        while True:
            await asyncio.sleep(60)
            logger.info(f"Remaining requests: {self._remaining_reqs}")

    async def _get_completion(
        self,
        conversation: List[Dict[str, str]],
        conversation_id: int,
    ) -> tuple[str | None, float]:
        # TODO: Ensure payload fits the context window
        payload = {
            "messages": conversation,
            **self._inference_config,
        }

        # Requests are attempted in seuqnence, meaning that the latter
        # will likely be blocked more often
        max_attempts = conversation_id + 3
        logger = get_dagster_logger()

        for _ in range(max_attempts):
            await self._retry_event.wait()  # Wait if currently in retry mode

            try:
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
                        self._retry_event.clear()  # Block further requests
                        await asyncio.sleep(wait_time)  # Wait as advised by the server
                        self._retry_event.set()  # Allow requests again
                    continue

                response.raise_for_status()
                res = response.json()
                answer: str = res["choices"][0]["message"]["content"]
                cost = (res["usage"]["prompt_tokens"] * self._input_cpm / 1000) + (
                    res["usage"]["completion_tokens"] * self._output_cpm / 1000
                )
                return answer, cost

            except httpx.TimeoutException as e:
                logger.error(f"LLM completion #{conversation_id} timed out: {e}")
                return None, 0
            except httpx.ReadError as e:
                logger.error(f"LLM completion #{conversation_id} timed out: {e}")
                return None, 0
            except Exception as e:
                logger.error(f"Error in LLM completion #{conversation_id}: {e}")
                return None, 0

        logger.error(
            f"Failed to get completion #{conversation_id} after {max_attempts} attempts."
        )
        return None, 0

    async def _get_prompt_sequence_completion(
        self, prompts_sequence: PromptSequence, conversation_id: int
    ) -> tuple[list[Dict[str, str]], float]:
        conversation: List[Dict[str, str]] = []
        total_cost = 0.0

        for prompt in prompts_sequence:
            if callable(prompt):
                content = prompt(conversation[-1]["content"])
            else:
                content = prompt

            conversation.append({"role": "user", "content": content})
            response, cost = await self._get_completion(conversation, conversation_id)
            self._remaining_reqs -= 1
            if not response:
                return [], total_cost
            else:
                conversation.append({"role": "assistant", "content": response})
                total_cost += cost

        return conversation, total_cost

    async def get_prompt_sequences_completions(
        self, prompt_sequences: List[PromptSequence]
    ) -> tuple[List[List[str]], float]:
        self._remaining_reqs = len(prompt_sequences) * len(prompt_sequences[0])
        self._status_printer_task = asyncio.create_task(self._periodic_status_printer())
        """
        This method is used to get completions for multiple prompt sequences in parallel.
        Prompt sequence items (other than the first in the list) can be callables that take
        the previous assistant response as input and return the next user prompt based on custom logic"""
        results = await asyncio.gather(
            *(
                self._get_prompt_sequence_completion(prompt_sequence, i)
                for i, prompt_sequence in enumerate(prompt_sequences)
            )
        )

        self._status_printer_task.cancel()
        await self._client.aclose()

        conversations = [conv for conv, cost in results]
        costs = [cost for conv, cost in results]

        # Assume all prompt sequences have the same length
        prompt_sequences_length = max(len(sequence) for sequence in prompt_sequences)

        # Return all the assistant responses, only for completed conversations
        return list(
            map(
                lambda x: [message["content"] for message in x[1::2]]
                if len(x) == prompt_sequences_length * 2
                else [],
                conversations,
            )
        ), sum(costs)
