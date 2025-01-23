import json

from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from data_pipeline.resources.graph_explorer_agent.prompts import AGENT_SYSTEM_PROMPT
from data_pipeline.resources.graph_explorer_agent.types import (
    ActionsImpl,
    HypothesisValidationResult,
    TraceRecord,
)

DEEPSEEK_INPUT_COST_1M = 0.55
DEEPSEEK_OUTPUT_COST_1M = 2.19


class GraphExplorerAgent:
    _client: OpenAI
    _messages: list[ChatCompletionMessageParam]
    _trace: list[TraceRecord]

    def __init__(
        self,
        api_key: str,
        system_prompt: str | None = None,
    ):
        self._client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self._messages = [
            {"role": "system", "content": system_prompt or AGENT_SYSTEM_PROMPT},
        ]
        self._trace = []

    @staticmethod
    def _calculate_cost(
        usage: CompletionUsage | None
    ) -> tuple[float | None, float | None]:
        if not usage:
            return None, None

        return (
            (usage.completion_tokens / 1_000_000) * DEEPSEEK_OUTPUT_COST_1M,
            (usage.prompt_tokens / 1_000_000) * DEEPSEEK_INPUT_COST_1M,
        )

    def _next_step(self, new_question: str) -> str | None:
        response = self._client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self._messages,
        )

        input_cost, output_cost = self._calculate_cost(response.usage)

        # Save the user message and trace it
        self._messages.append({"role": "user", "content": new_question})
        self._trace.append(
            TraceRecord(
                role="user",
                content=new_question,
                reasoning_content=None,
                cost=input_cost,
            )
        )

        # Save the assistant message and trace it
        answer = response.choices[0].message.content
        self._messages.append({"role": "assistant", "content": answer})
        self._trace.append(
            TraceRecord(
                role="assistant",
                content=answer,
                reasoning_content=response.choices[0].message.reasoning_content,  # type: ignore
                cost=output_cost,
            )
        )

        return answer

    @staticmethod
    def _parse_agent_response(
        response: str, actions_impl: ActionsImpl
    ) -> tuple[HypothesisValidationResult | None, list | None]:
        """Parse agent response and execute any actions.

        Returns:
            tuple: (final_result, action_results)
                - final_result: HypothesisValidationResult if final result found, None otherwise
                - action_results: List of action results if actions executed, None otherwise
        """
        try:
            result = json.loads(response)

            # Check for final result
            if "result" in result:
                return HypothesisValidationResult(**result["result"]), None

            # Parse and execute actions
            if "actions" in result:
                action_results = []
                for action in result["actions"]:
                    if not hasattr(actions_impl, action["name"]):
                        raise ValueError(f"Unknown action: {action['name']}")

                    # Execute the action and get result
                    result = getattr(actions_impl, action["name"])(**action["args"])

                    action_results.append(
                        {
                            "action": action["name"],
                            "args": action["args"],
                            "result": result,
                        }
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
        final_result = None
        action_results = None
        iteration = 0

        while final_result is None:
            if action_results:
                self._next_step(f"Action results: {json.dumps(action_results)}")
            else:
                if iteration == 0:
                    self._next_step(f"Here is the hypothesis to validate: {hypothesis}")
                else:
                    raise ValueError("Failed to get action results")

            response = self._next_step(hypothesis)

            if not response:
                raise ValueError("Failed to get response from the model")

            final_result, action_results = self._parse_agent_response(
                response, actions_impl
            )
            iteration += 1

        return final_result, self._trace
