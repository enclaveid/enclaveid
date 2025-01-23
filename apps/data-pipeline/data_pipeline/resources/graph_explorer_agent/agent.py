import json
from typing import Callable, cast

from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from opik.integrations.openai import track_openai

from data_pipeline.resources.graph_explorer_agent.prompts import AGENT_SYSTEM_PROMPT


class GraphExplorerAgent:
    client: OpenAI
    messages: list[ChatCompletionMessageParam]
    actions: dict[str, Callable]

    def __init__(
        self,
        api_key: str,
        actions: dict[str, Callable],
        system_prompt: str | None = None,
    ):
        self.client = cast(
            OpenAI,
            track_openai(OpenAI(api_key=api_key, base_url="https://api.deepseek.com")),
        )
        self.actions = actions
        self.messages = [
            {"role": "system", "content": system_prompt or AGENT_SYSTEM_PROMPT},
        ]

    def _next_step(self, new_question: str) -> str | None:
        self.messages.append({"role": "user", "content": new_question})

        response = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self.messages,
        )

        answer = response.choices[0].message.content

        # Reasoning tokens
        # reasoning = response.choices[0].message.reasoning_content
        # Cost calculation
        # response.usage.completion_tokens * output_cost + response.usage.prompt_tokens * input_cost

        self.messages.append({"role": "assistant", "content": answer})

        return answer

    @staticmethod
    def _parse_agent_response(
        response: str, actions: dict[str, Callable]
    ) -> tuple[dict | None, list | None]:
        """Parse agent response and execute any actions.

        Returns:
            tuple: (final_result, action_results)
                - final_result: Dict if final result found, None otherwise
                - action_results: List of action results if actions executed, None otherwise
        """
        try:
            result = json.loads(response)

            # Check for final result
            if "result" in result:
                return result["result"], None

            # Parse and execute actions
            if "actions" in result:
                action_results = []
                for action in result["actions"]:
                    if action["name"] not in actions:
                        raise ValueError(f"Unknown action: {action['name']}")

                    # Execute the action and get result
                    result = actions[action["name"]](**action["args"])
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

    def validate_hypothesis(self, hypothesis: str) -> dict:
        final_result = None
        action_results = None
        iteration = 0

        while final_result is None:
            if action_results:
                self._next_step(f"Action results: {json.dumps(action_results)}")
            else:
                self._next_step(f"Here is the hypothesis to validate: {hypothesis}")

            response = self._next_step(hypothesis)

            if not response:
                raise ValueError("Failed to get response from the model")

            final_result, action_results = self._parse_agent_response(
                response, self.actions
            )
            iteration += 1

        return final_result
