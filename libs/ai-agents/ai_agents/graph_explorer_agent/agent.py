import inspect
import json
import re
from dataclasses import asdict

from json_repair import repair_json

from ..base_agent import BaseAgent, TraceRecord
from .prompts import (
    GRAPH_EXPLORER_AGENT_SYSTEM_PROMPT,
)
from .types import (
    ActionResult,
    ActionsImpl,
    AdjacencyList,
    HypothesisValidationResult,
)


class GraphExplorerAgent(BaseAgent):
    def __init__(
        self,
        model_config,
        system_prompt: str | None = None,
    ):
        super().__init__(
            model_config, system_prompt or GRAPH_EXPLORER_AGENT_SYSTEM_PROMPT
        )

    async def _parse_agent_response(
        self,
        response: str,
        actions_impl: ActionsImpl,
    ) -> HypothesisValidationResult | list[ActionResult]:
        """Parse agent response and execute any actions.

        Returns:
            tuple: (final_result, action_results)
                - final_result: HypothesisValidationResult if final result found, None otherwise
                - action_results: List of action results if actions executed, None otherwise
        """
        try:
            # The LLM often returns json within markdown code blocks
            json_match = re.search(
                r"```(?:json)?\s*([\s\S]*?)\s*```", response, re.DOTALL
            )
            # If no json match, just use the response as is
            cleaned_response = (
                json_match.group(1).strip() if json_match else response.strip()
            )

            result: dict = repair_json(cleaned_response, return_objects=True)  # type: ignore

        except Exception as e:
            raise ValueError(
                f"Failed to parse agent response: {cleaned_response}"
            ) from e

        # Check for final result
        if "result" in result:
            return HypothesisValidationResult(**result["result"])
        # Parse and execute actions
        elif "actions" in result:
            # Discard malformed actions
            result["actions"] = [
                a
                for a in result["actions"]
                if (
                    "name" in a
                    and isinstance(a["name"], str)
                    and "args" in a
                    and isinstance(a["args"], dict)
                )
            ]

            action_results = []
            for action in result["actions"]:
                if not hasattr(actions_impl, action["name"]):
                    raise ValueError(f"Unknown action: {action['name']}")

                # Execute the action and get result
                try:
                    action_fn = getattr(actions_impl, action["name"])
                    # Await if the action is async
                    if inspect.iscoroutinefunction(action_fn):
                        action_result: AdjacencyList = await action_fn(**action["args"])
                    else:
                        action_result: AdjacencyList = action_fn(**action["args"])
                except Exception as e:
                    raise ValueError(
                        f"Failed to execute action: {action['name']} with args: {action['args']}"
                    ) from e

                action_results.append(
                    ActionResult(
                        action=action["name"],
                        args=action["args"],
                        result=action_result,
                    )
                )
            return action_results
        else:
            raise ValueError(
                f"Agent response does not contain a result or actions: {cleaned_response}"
            )

    async def validate_hypothesis(
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
                self._logger.info(f"[ACTIONS_RESULTS] \n{formatted_action_results}\n")
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

            res = await self._parse_agent_response(response, actions_impl)

            if isinstance(res, HypothesisValidationResult):
                final_result = res
            else:
                action_results = res

            iteration += 1

        return final_result, self._trace
