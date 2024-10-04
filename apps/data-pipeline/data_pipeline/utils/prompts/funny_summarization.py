import random


def _get_quirky_aspects_prompt(search_activity: str):
    return f"""
    Analyze the provided cluster of internet activity data for a single topic.
    What are its most funny, unique or quirky aspects?
    Keep in mind that there might have been some errors during the clustering, so some completely unrelated records might appear.
    Conclude your answer with a small summary of what you learned about the user.

    {search_activity}
    """


HUMOR_CATEGORIES = [
    "satirical and offensive humor (do your worst!)",
    "benign violation",
    "superiority theory",
    "incongruity theory",
]


def _get_one_liner_with_image_prompt():
    humor_category = random.choice(HUMOR_CATEGORIES)
    return f"""
    Generate a funny one-liner and a title for the humor category: {humor_category}.
    The humor has to pivot on the person behind this activity.
    Finally, provide an image description exemplifying the humor. The image has to be photorealistic, yet ridiculous.
    Format your answer in json: {{"title": str, "description": str, "image": str}}
    """


def get_funny_summarization_prompt_sequence(search_activity: str):
    return [
        _get_quirky_aspects_prompt(search_activity),
        _get_one_liner_with_image_prompt(),
    ]
