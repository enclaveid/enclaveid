from pydantic import BaseModel


def get_assistant_responses(
    conversations: list[list[dict[str, str]]]
) -> list[list[str | BaseModel]]:
    """
    Return all the assistant responses, only for completed conversations.
    We assume that all prompt sequences have the same length.
    """
    prompt_sequences_length = max(map(len, conversations))

    return list(
        map(
            lambda x: [message["content"] for message in x[1::2]]
            if len(x) == prompt_sequences_length
            else [],
            conversations,
        )
    )
