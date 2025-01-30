import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

import httpx
from dagster import get_dagster_logger
from json_repair import repair_json

from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig
from data_pipeline.resources.graph_explorer_agent.prompts import AGENT_SYSTEM_PROMPT
from data_pipeline.resources.graph_explorer_agent.types import (
    ActionResult,
    ActionsImpl,
    AdjacencyList,
    HypothesisValidationResult,
    TraceRecord,
)


class GraphExplorerAgent:
    _client: httpx.Client
    _messages: list[Dict[str, Any]]
    _trace: list[TraceRecord]
    _model_config: RemoteLlmConfig

    def __init__(
        self,
        model_config: RemoteLlmConfig,
        system_prompt: str | None = None,
    ):
        self._client = httpx.Client(
            timeout=model_config.timeout,
        )
        self._messages = [
            {"role": "system", "content": system_prompt or AGENT_SYSTEM_PROMPT},
        ]
        self._trace = []
        self._logger = get_dagster_logger()
        self._model_config = model_config

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
    def _get_reasoning_content(response: Dict[str, Any]) -> str | None:
        reasoning_content = response["choices"][0]["message"].get(
            "reasoning_content", None
        )

        # Look for content between <think> tags if reasoning_content is not available directly
        if reasoning_content is None:
            content = response["choices"][0]["message"]["content"]
            start_tag = "<think>"
            end_tag = "</think>"
            start_idx = content.find(start_tag)
            end_idx = content.find(end_tag)

            if start_idx != -1 and end_idx != -1:
                reasoning_content = content[
                    start_idx + len(start_tag) : end_idx
                ].strip()

        return reasoning_content

    def _next_step(self, new_question: str) -> str | None:
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

        # Save the assistant response
        answer = result["choices"][0]["message"]["content"]
        self._messages.append({"role": "assistant", "content": answer})

        # Trace the user message
        self._trace.append(
            TraceRecord(
                role="user",
                content=new_question,
                reasoning_content=None,
                cost=input_cost,
                timestamp=datetime.now(),
            )
        )

        # Trace the assistant response with reasoning content if available
        reasoning_content = self._get_reasoning_content(result)
        self._trace.append(
            TraceRecord(
                role="assistant",
                content=answer,
                reasoning_content=reasoning_content,
                cost=output_cost,
                timestamp=datetime.now(),
            )
        )

        return answer

    def _parse_agent_response(
        self,
        response: str,
        actions_impl: ActionsImpl,
    ) -> tuple[HypothesisValidationResult | None, list | None]:
        """Parse agent response and execute any actions.

        Returns:
            tuple: (final_result, action_results)
                - final_result: HypothesisValidationResult if final result found, None otherwise
                - action_results: List of action results if actions executed, None otherwise
        """
        try:
            result: dict = repair_json(response, return_objects=True)  # type: ignore

            # Check for final result
            if "result" in result:
                return HypothesisValidationResult(**result["result"]), None

            # Parse and execute actions
            if "actions" in result:
                self._logger.info(
                    f"[ACTIONS] {json.dumps(result['actions'], indent=2)}"
                )
                action_results = []
                for action in result["actions"]:
                    if not hasattr(actions_impl, action["name"]):
                        raise ValueError(f"Unknown action: {action['name']}")

                    # Execute the action and get result
                    action_result: AdjacencyList = getattr(
                        actions_impl, action["name"]
                    )(**action["args"])

                    action_results.append(
                        ActionResult(
                            action=action["name"],
                            args=action["args"],
                            result=action_result,
                        )
                    )
                return None, action_results

            return None, None

        except json.JSONDecodeError:
            return None, None

    def validate_hypothesis(
        self,
        hypothesis: str,
        actions_impl: ActionsImpl,
    ) -> tuple[HypothesisValidationResult | None, list[TraceRecord] | None]:
        final_result: HypothesisValidationResult | None = None
        action_results: list[ActionResult] | None = None
        iteration = 0

        while final_result is None:
            if action_results:
                formatted_action_results = json.dumps(
                    [asdict(ar) for ar in action_results], indent=2
                )
                self._logger.info(f"[ACTION RESULTS] \n{formatted_action_results}\n")
                response = self._next_step(
                    f"Action results: {formatted_action_results}"
                )
            else:
                if iteration == 0:
                    response = self._next_step(
                        f"Here is the hypothesis to validate: {hypothesis}"
                    )
                else:
                    raise ValueError(
                        f"Failed to get action results in iteration #{iteration}"
                    )

            if not response:
                raise ValueError(
                    f"Failed to get response from the model in iteration #{iteration}"
                )

            final_result, action_results = self._parse_agent_response(
                response, actions_impl
            )
            iteration += 1

        return final_result, self._trace
