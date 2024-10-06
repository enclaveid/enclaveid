from textwrap import dedent


def _get_initial_analysis_prompt(search_activity: str):
    return dedent(
        f"""
      Here is a list of chronologically ordered activities from my internet activity around a given topic.
      Provide a description for the patterns as well as the content, and include the most detailed possible category that captures all the topics of the activity.
      Finally determine if the topic is sensitive from a psychosocial angle.

      {search_activity}
    """
    ).strip()


ASPECTS_PROMPT = dedent(
    """
      From this analysis, return the most diverse set of culturally relevant "aspects".
      Consider both 1. a Serious & Substantive angle, and 2. a more Quirky & Cultural one.
      For example, such a set of  "aspects" of "cat" is:
      - Pointy ears
      - Night vision
      - Fur
      - Paws
      - Lazy
      - Small creatures
      - Pets
      - Things that bring bad luck
      - Things that sound like "bat"
      - Things that sleep on my couch
    """
).strip()

FORMATTING_INSTRUCTIONS = dedent(
    """
    Format your answer in json as follows:
    {{
      “descriptive_category”: string,
      "senstivity": float from 0 to 1,
      “all_aspects”: array of strings
    }}
    """
).strip()


def get_aspects_summarization_prompt_sequence(search_activity: str):
    return [
        _get_initial_analysis_prompt(search_activity),
        ASPECTS_PROMPT,
        FORMATTING_INSTRUCTIONS,
    ]
