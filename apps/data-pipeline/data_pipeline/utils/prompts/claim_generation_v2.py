from textwrap import dedent
from typing import Any, Dict, List

from json_repair import repair_json


def _get_inferrables_prompt(search_activity: str):
    return dedent(
        f"""
        Here is a cluster of my search activity around a given topic.
        Your task is to identify a set of "inferrables" about the topic and the activity.

        First off, infer if the activity is primarily driven by:
        1. A progression in knowledge acquisition and long-term interest, or
        2. Reactive searches driven by occasional or recurring needs.

        Consider the following factors in your analysis:
        - Frequency and regularity of searches
        - Diversity of subtopics within the main theme
        - Presence of time-bound or event-specific queries
        - Indications of recurring but intermittent activities
        - Signs of problem-solving for specific occasions rather than general learning

        Secondly, proceed with the identification of inferrables.
        An inferrable is a deduction with the following characteristics:
        - "What we can reasonably conclude given the data"
        - Like a detective looking at evidence and making solid deductions
        - Requires some expertise/context to make the connection
        - Most qualified observers would reach similar conclusions
        - The claim can be made with a medium to high degree of confidence

        Make sure to limit the object of the inference to the topic and activity, not me.

        Here is the cluster of search activity:
        {search_activity}
        """
    ).strip()


SPECULATIVES_PROMPT = dedent(
    """
    Now, identify a set of "speculatives" about me in relation to the activity performed.
    Speculatives have the following characteristics:
    - "What might be true given what we know"
    - Like a psychologist understanding someone's motivations from their actions
    - Requires understanding human/organizational behavior
    - Different observers might reach different conclusions

    These should be as varied and ambitious as possible, for example:
    - Intrinsic and extrinsic motivators
    - Cognitive biases and personality traits
    - Broad contextual and situational factors

    Do not worry about them potentially being low confidence as we will attempt to substantiate them at a later time.
    """
).strip()

FORMATTING_INSTRUCTIONS = dedent(
    """
    Format your answers as a JSON object with the following keys:

    {
        "inferrables": [
            {"claim": string, "confidence": float, "from_date": yyyy-mm-dd, "to_date": yyyy-mm-dd},
            ...
        ],
        "speculatives": [
            {"claim": string, "confidence": float, "from_date": yyyy-mm-dd, "to_date": yyyy-mm-dd},
            ...
        ],
    }

    One or both dates for each claim can be empty if the claim is unbound in the past and/or future.
    """
).strip()


def get_claim_generation_prompt_sequence(search_activity: str):
    return [
        _get_inferrables_prompt(search_activity),
        SPECULATIVES_PROMPT,
        FORMATTING_INSTRUCTIONS,
    ]


def parse_claims_json(text: str, cluster_label: int) -> List[Dict[str, Any]] | None:
    try:
        j = repair_json(text, return_objects=True)
        if isinstance(j, dict) and "inferrables" in j and "speculatives" in j:
            claims = []
            for claim in j["inferrables"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": claim.get("confidence", 0.0),
                        "claim_type": "inferrable",
                        "cluster_label": cluster_label,
                    }
                )
            for claim in j["speculatives"]:
                claims.append(
                    {
                        "from_date": claim.get("from_date"),
                        "to_date": claim.get("to_date"),
                        "claim": claim["claim"],
                        "confidence": claim.get("confidence", 0.0),
                        "claim_type": "speculative",
                        "cluster_label": cluster_label,
                    }
                )
            return claims
    except Exception:
        return None
