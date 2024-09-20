from datetime import datetime
from textwrap import dedent

from data_pipeline.utils.parsing.json import parse_cluster_classification_json


def _get_initial_classification_prompt(search_activity: str):
    return dedent(
        f"""
        Analyze the provided cluster of search activity data for a single topic. Determine whether this cluster primarily represents:
        1. A progression in knowledge acquisition and long-term interest, or
        2. Reactive searches driven by occasional or recurring needs.

        Consider the following factors in your analysis:
        - Frequency and regularity of searches
        - Diversity of subtopics within the main theme
        - Presence of time-bound or event-specific queries
        - Indications of recurring but intermittent activities
        - Signs of problem-solving for specific occasions rather than general learning

        Provide a classification as either 'knowledge_progression' or 'reactive_needs', along with a confidence score (0-100%).
        Offer a an explaination supporting your classification, highlighting the key factors that influenced your decision.
        Additionally, assess whether the topic is sensitive in nature, particularly regarding psychosocial aspects.

        Conclude your analysis with a JSON as follows:
        {{
          "activity_type": "knowledge_progression" or "reactive_needs" or "unknown",
          "sensitive": true or false,
          "confidence": 0.0-1.0
        }}

        {search_activity}
        """
    )


def _get_summarization_prompt(initial_classification_result: str) -> str:
    CLUSTER_SUMMARIZATION_FORMAT = dedent(
        """
        Pay particular attention to the elements tagged as "QUIRKY" in the cluster, and make sure to mention them in the summary.

        Finally, provide the most detailed possible category that captures all the topics of the activity.

        Conclude your analysis with a JSON as follows:
        {
          "title": "The category you found",
          "summary": "Your summary"
        }
        """
    )

    UNKNOWN_SUMMARY = dedent(
        """
        The search activity does not fit the criteria for either knowledge progression or reactive needs.
        Explain why the activity is ambiguous and provide a brief summary of the main topics covered.

        {CLUSTER_SUMMARIZATION_FORMAT}
        """
    )

    key = parse_cluster_classification_json(initial_classification_result)[0]

    if key is None:
        return UNKNOWN_SUMMARY
    else:
        return {
            "unknown": UNKNOWN_SUMMARY,
            "reactive_needs": dedent(
                f"""
              Summarize the reactive search activity by taking into account the time periods
              and what the user will have obtained at the end of their search. Describe:

              - The main category of reactive needs
              - The specific types of occasions or needs
              - Frequency pattern of these needs
              - User's apparent level of experience in addressing these needs

              {CLUSTER_SUMMARIZATION_FORMAT}
              """
            ),
            "knowledge_progression": dedent(
                f"""
              Summarize the knowledge progression by taking into account the time periods and how each
              incremental chunk expands the user's knowledge horizontally or vertically. Describe:

              - The main topic or starting point of interest
              - Key areas or subtopics the user explored from this starting point
              - How the user's understanding seemed to deepen or branch out in each area
              - Any connections or jumps between different areas of exploration
              - The most advanced or recent concepts the user has searched for

              Conclude with the overall trajectory and breadth of the user's learning path.

              {CLUSTER_SUMMARIZATION_FORMAT}
              """
            ),
        }[key]


SOCIAL_LIKELIHOOD_PROMPT = dedent(
    f"""
        Would this type of activity be interesting to connect over with other similar users?
        In your analysis, take into account:
        - [IMPORTANT] Whether the topic itself is generally boring (e.g., main job, taxation, laundry) or engaging (e.g., arts, games, hobbies)
        - How deeply engaged the user seems to be with the topic
        - Whether the user engaged in very niche areas of the topic
        - If the activity is sensitive, assume the user is willing to share it with others
        - The current date is {datetime.today().strftime('%Y-%m-%d')}, if the activity is reactive, consider that it might not be relevant for the user if they did it long ago

        Provide a social likelihood score from 0 to 100% in JSON as follows:
        {{
          "likelihood": 0.0 - 1.0,
        }}
        """
)


def get_summarization_prompt_sequence(search_activity: str):
    return [
        _get_initial_classification_prompt(search_activity),
        _get_summarization_prompt,
        SOCIAL_LIKELIHOOD_PROMPT,
    ]
