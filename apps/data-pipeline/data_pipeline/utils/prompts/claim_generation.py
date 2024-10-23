from textwrap import dedent


def _get_initial_analysis_prompt(
    search_activity: str, year_start: int, year_end: int, records_count: int
):
    return dedent(
        f"""
        Analyze the provided cluster of my search activity data for a single topic.
        Keep in mind that this is extracted from a broader dataset of activities from {year_start} to {year_end} with about {records_count} records in total.

        {search_activity}
        """
    ).strip()


CLAIM_GENERATION_PROMPT = dedent(
    """
    What claims can you make about me from this analysis?
    Separate the claims into strong, factual (what, when) and weak, speculative (why).
    Try to make your weak claims as varied and ambitious as possible even if it results
    in low confidence, trying to cover as many aspects of myself as possible.
    """
    # If a weak claim has more than 70% confidence, include it in the strong claims.
).strip()

FORMATTING_INSTRUCTIONS = dedent(
    """
    Format your answer in json as follows:

    {{
        "strong": [
            {{
                "claim": string,
                "from_date": string,
                "to_date": string
            }}
        ],
        "weak": [
            {{
                "claim": string,
                "from_date": string,
                "to_date": string,
                "confidence": float
            }}
        ]
    }}
    """
).strip()


def get_claim_generation_prompt_sequence(
    search_activity: str, year_start: int, year_end: int, records_count: int
):
    return [
        _get_initial_analysis_prompt(
            search_activity, year_start, year_end, records_count
        ),
        CLAIM_GENERATION_PROMPT,
        FORMATTING_INSTRUCTIONS,
    ]
