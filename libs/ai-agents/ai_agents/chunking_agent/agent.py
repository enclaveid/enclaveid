from dataclasses import dataclass
from textwrap import dedent
from typing import Callable, Literal

from json_repair import repair_json

from ..base_agent import BaseAgent, TraceRecord
from .prompts import (
    CHUNKING_AGENT_FORCE_SPLIT_PROMPT,
    CHUNKING_AGENT_SPLIT_PROMPT,
)


@dataclass
class ChunkDecision:
    decision: Literal["SPLIT", "NO_SPLIT"]
    timestamp: str | None
    sentiment: float | None


class ChunkingAgent(BaseAgent):
    def __init__(
        self,
        model_config,
    ):
        super().__init__(model_config, with_memory=False)

    def _parse_llm_response(
        self,
        response: str,
    ) -> ChunkDecision:
        try:
            result: dict = repair_json(response, return_objects=True)  # type: ignore

            return ChunkDecision(**result)
        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {response}") from e

    def chunk_messages(
        self,
        next_chunk: Callable[..., tuple[str | None, bool]],
    ) -> list[TraceRecord]:
        to_process, is_over_max_size = next_chunk()
        max_retries = 3
        retries = 0

        while to_process is not None:
            try:
                llm_response = self._next_step(
                    dedent(
                        f"""
                      {CHUNKING_AGENT_SPLIT_PROMPT if not is_over_max_size else CHUNKING_AGENT_FORCE_SPLIT_PROMPT}

                      Here is the list of messages:
                      {to_process}
                      """
                    )
                )

                if llm_response is None:
                    raise ValueError("No LLM response received")

                chunk_decision = self._parse_llm_response(llm_response)

                to_process, is_over_max_size = next_chunk(chunk_decision)
                retries = 0
            except Exception as e:
                retries += 1
                self._logger.error(f"Error processing chunk: {e}, retrying...")
                if retries > max_retries:
                    raise ValueError(
                        f"Failed to process chunk after {max_retries} retries"
                    ) from e

        return self._trace
