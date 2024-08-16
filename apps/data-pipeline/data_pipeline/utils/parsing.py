import re


def remove_markdown(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text


def _extract_text(text, pattern, default=None) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default


def _extract_number(text, pattern, default=0.0) -> float:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default


def _extract_boolean(text, pattern, default=None) -> bool | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).lower() == "true" if match else default


def parse_classification_result(raw_output: str):
    clean_output = remove_markdown(raw_output)

    classification = _extract_text(clean_output, r"Classification:\s*(.+?)(?:\n|$)")
    confidence = (
        _extract_number(clean_output, r"Confidence:\s*(\d+(?:\.\d+)?)%") / 100.0
    )
    is_sensitive = _extract_boolean(
        clean_output, r"Sensitive:\s*(true|false|True|False)"
    )
    explanation = _extract_text(clean_output, r"Explanation:\s*(.+)(?:\n\n|\Z)")

    parsed_classification = (
        None
        if classification is None
        else {
            "classification": classification,
            "confidence": confidence,
            "explanation": explanation,
        }
    )

    main_category = "unknown"
    if parsed_classification and confidence >= 0.5:
        classification_lower = classification.lower()
        if "knowledge progression" in classification_lower:
            main_category = "proactive"
        elif "reactive needs" in classification_lower:
            main_category = "reactive"

    return main_category, is_sensitive


def parse_cluster_summarization(raw_output: str):
    clean_output = remove_markdown(raw_output)

    title = _extract_text(clean_output, r"Title:\s*(.+?)(?:\n|$)")
    summary = _extract_text(clean_output, r"Summary:\s*(.+)(?:\n\n|\Z)")

    return title, summary


def parse_social_likelihood(raw_output: str):
    clean_output = remove_markdown(raw_output)

    return _extract_number(clean_output, r"Likelihood:\s*(\d+(?:\.\d+)?)%") / 100.0
