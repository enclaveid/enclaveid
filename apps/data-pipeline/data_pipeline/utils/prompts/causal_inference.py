from textwrap import dedent
from typing import Any, Dict

from json_repair import repair_json

SUBCLUSTERING_PROMPT = dedent(
    """
    Given a chronological list of activities, identify distinct thematic clusters:
    - Create clusters based on results/outcomes of the activity, not the activities themselves
    - Each cluster description should be self-contained
    - Avoid cross-referencing between clusters
    - Each cluster should span the minimum possible time window in which most of the activity is concentrated

    Make sure to split activities into separate clusters if they are unrelated, even if they are close in time.

    Here is the list of activities:
    {activities}
    """
).strip()

WITHIN_CLUSTER_CAUSAL_INFERENCE_PROMPT = dedent(
    """
    Now construct a narrative that:

    - Identifies potential causal relationships between clusters, while noting which clusters appear independent
    - Explains how earlier clusters influenced later ones, avoiding assumptions based solely on timing
    - Highlights key transition points where focus shifted
    - Points out parallel developments, distinguishing between related vs merely concurrent activities

    The narrative should balance:

    - What can be directly inferred from timing and content
    - Reasonable speculation based on the activity data
    - Alternative explanations where causation is ambiguous (speculate on out of list context)
    - External factors that might independently influence multiple clusters

    Focus on telling a coherent story of how the activity evolved over time, while acknowledging uncertainty where appropriate.
    Avoid using symbolic references to the subclusters, instead use the actual times and descriptions.
    """
).strip()

FORMATTING_INSTRUCTIONS = dedent(
    """
    Format your previous answer in json as follows:
    {
      "subclusters": [
        {
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "description": string
        }
      ]
    }
    """
).strip()


def parse_causal_inference_json(text: str) -> Dict[str, Any] | None:
    try:
        j = repair_json(text, return_objects=True)
        if isinstance(j, dict) and "subclusters" in j:
            return {
                "subclusters": j["subclusters"],
            }
    except Exception:
        return None


def get_causal_inference_prompt_sequence(activities: str):
    return [
        SUBCLUSTERING_PROMPT.format(activities=activities),
        # WITHIN_CLUSTER_CAUSAL_INFERENCE_PROMPT,
        FORMATTING_INSTRUCTIONS,
    ]


if __name__ == "__main__":
    for x in get_causal_inference_prompt_sequence("TEST"):
        print(x)
        print("---------")
