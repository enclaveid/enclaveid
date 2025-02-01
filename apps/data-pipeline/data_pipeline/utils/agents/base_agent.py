import re
from dataclasses import dataclass
from datetime import datetime
from logging import Logger
from typing import Any, Dict, Tuple

import httpx
from dagster import get_dagster_logger

from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig


@dataclass
class TraceRecord:
    role: str
    content: str
    reasoning_content: str | None
    cost: float | None
    token_count: int
    timestamp: datetime


class BaseAgent:
    _messages: list[dict[str, Any]] = []
    _trace: list[TraceRecord] = []
    _system_prompt: str | None = None

    _logger: Logger
    _model_config: RemoteLlmConfig
    _with_memory: bool

    def __init__(
        self,
        model_config: RemoteLlmConfig,
        system_prompt: str | None = None,
        with_memory: bool = True,
    ):
        if system_prompt:
            self._system_prompt = system_prompt
            self._messages.append({"role": "system", "content": system_prompt})

        self._client = httpx.Client(
            timeout=model_config.timeout,
        )
        self._logger = get_dagster_logger()
        self._model_config = model_config
        self._with_memory = with_memory

    def _calculate_cost(
        self,
        usage: Dict[str, int],
    ) -> tuple[float | None, float | None]:
        if not usage:
            return None, None

        return (
            (usage["completion_tokens"] / 1_000_000) * self._model_config.output_cpm,
            (usage["prompt_tokens"] / 1_000_000) * self._model_config.input_cpm,
        )

    @staticmethod
    def _get_answer(response: Dict[str, Any]) -> Tuple[str, str | None]:
        answer = response["choices"][0]["message"]["content"]

        reasoning_content = response["choices"][0]["message"].get(
            "reasoning_content", None
        )

        if reasoning_content is None:
            think_pattern = r"<think>(.*?)</think>"
            think_match = re.search(think_pattern, answer, re.DOTALL)

            if think_match:
                reasoning_content = think_match.group(1).strip()
                answer = re.sub(think_pattern, "", answer, flags=re.DOTALL).strip()

        return answer, reasoning_content

    def _next_step(self, new_question: str) -> str | None:
        if not self._with_memory:
            if self._system_prompt:
                self._messages = [{"role": "system", "content": self._system_prompt}]
            else:
                self._messages = []

        self._messages.append({"role": "user", "content": new_question})

        payload = {
            "messages": self._messages,
            **self._model_config.inference_config,
        }

        if self._model_config.provider:
            payload["provider"] = self._model_config.provider

        response = self._client.post(
            self._model_config.inference_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._model_config.api_key}",
                "api-key": self._model_config.api_key,
            },
        )
        response.raise_for_status()
        result = response.json()

        input_cost, output_cost = self._calculate_cost(result["usage"])

        answer, reasoning_content = self._get_answer(result)
        self._messages.append({"role": "assistant", "content": answer})

        self._trace.append(
            TraceRecord(
                role="user",
                content=new_question,
                reasoning_content=None,
                cost=input_cost,
                token_count=result["usage"]["prompt_tokens"],
                timestamp=datetime.now(),
            )
        )

        self._trace.append(
            TraceRecord(
                role="assistant",
                content=answer,
                reasoning_content=reasoning_content,
                cost=output_cost,
                token_count=result["usage"]["completion_tokens"],
                timestamp=datetime.now(),
            )
        )

        return answer
