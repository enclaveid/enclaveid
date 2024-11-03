from textwrap import dedent

CROSS_CHUNK_CAUSAL_INFERENCE_PROMPT = dedent(
    """
    Here is a list of activities for a given day.

    Construct a narrative that:
    - Identifies potential causal relationships between activities
    - Explains how earlier activities influenced later ones, avoiding assumptions based solely on timing

    The narrative should balance:
    - What can be directly inferred from timing and content
    - Reasonable speculation based on the activity data
    - Alternative explanations where causation is ambiguous (speculate on unknown context)

    Focus on telling a coherent story of how the activity evolved over time.
    Use symbolic references to the activities (count from 0), but also include the actual times and descriptions.

    Most importantly, do not include in the narrative any activity that seems to be unrelated to the others or for which you cannot identify a causal relationship.

    {chunks}
    """
).strip()


def get_cross_chunk_causal_inference_prompt_sequence(chunks: list[str]):
    return [
        CROSS_CHUNK_CAUSAL_INFERENCE_PROMPT.format(chunks="\n".join(chunks)),
    ]
