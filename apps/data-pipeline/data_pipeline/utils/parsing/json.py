from typing import List

from json_repair import repair_json


def parse_cluster_categories_json(text) -> List[str]:
    try:
        j = repair_json(text, return_objects=True)
        res = j["cluster_categories"]
    except Exception:
        res = []

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
