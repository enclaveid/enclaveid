from textwrap import dedent

CHUNKING_AGENT_FORCE_SPLIT_PROMPT = dedent(
    """
    You will be given a list of interleaved messages around a given topic.
    Identify the timestamp that splits the discussion into two chunks that have the last possilbe amount of dependencies between them.

    Reason on your decision and conclude with a JSON as follows:
    {
      "decision": "SPLIT",
      "timestamp": "YYYY-MM-DD HH:MM:SS"
    }
   """
)

CHUNKING_AGENT_SPLIT_PROMPT = dedent(
    """
      Go through the following messages in order and identify the first timestamp of when you detect a topic change, or in other words, the messages after the timestamp are not dependent on the messages before the timestamp.
      Only do it for the first topic change you detect, no matter how many others you see.

      Tag your detection as follows:
      - "NO_SPLIT" if you cannot identify a topic change
      - "SPLIT" if you identify the first topic change

      Reason on your decision and conclude with a JSON as follows:
      {
        "decision": "NO_SPLIT" | "SPLIT",
        "timestamp": null | "YYYY-MM-DD HH:MM:SS"
      }
    """
)
