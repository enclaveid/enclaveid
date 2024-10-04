from typing import List

from json_repair import repair_json


def parse_category_json(text) -> str | None:
    try:
        j = repair_json(text, return_objects=True)
        res = j["descriptive_categorization"]
    except Exception:
        res = None

    return res


def parse_cluster_classification_json(text) -> tuple[str | None, bool | None]:
    try:
        j = repair_json(text, return_objects=True)
        res = j["activity_type"], j["sensitive"]
    except Exception:
        res = None, None

    return res


def parse_cluster_summarization_json(text) -> tuple[str | None, str | None]:
    try:
        j = repair_json(text, return_objects=True)
        res = j["title"], j["summary"]
    except Exception:
        res = None, None

    return res


def parse_social_likelihood_json(text) -> float | None:
    try:
        j = repair_json(text, return_objects=True)
        res = float(j["likelihood"])
        # Sometimes the llm return the percentage as integer
        if res > 1:
            res = res / 100
        return res
    except Exception:
        res = None

    return res


def parse_funny_summaries(text: str) -> tuple[str | None, str | None, str | None]:
    try:
        j = repair_json(text, return_objects=True)
        title = j["title"] if isinstance(j["title"], str) else None
        description = j["description"] if isinstance(j["description"], str) else None
        image = j["image"] if isinstance(j["image"], str) else None
        res = title, description, image
    except Exception:
        res = None, None, None

    return res


def parse_summaries_completions(summaries_completions: List[List[str]]):
    activity_types, sensitivities, titles, summaries, likelihoods = zip(
        *list(
            map(
                lambda x: (
                    *parse_cluster_classification_json(x[0]),
                    *parse_cluster_summarization_json(x[1]),
                    parse_social_likelihood_json(x[2]),
                )
                if x
                else (None, None, None, None, None),
                summaries_completions,
            )
        )
    )

    return {
        "activity_type": activity_types,
        "is_sensitive": sensitivities,
        "cluster_title": titles,
        "cluster_summary": summaries,
        "social_likelihood": likelihoods,
    }
