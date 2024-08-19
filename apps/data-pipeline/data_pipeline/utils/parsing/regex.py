import re

import numpy as np


def remove_markdown(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text


def _extract_text(text, pattern, default=None) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default


def _extract_number(text, pattern, default=-np.inf) -> float:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default


def _extract_boolean(text, pattern, default=None) -> bool | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).lower() == "true" if match else default


def parse_cluster_summarization(raw_output: str):
    title = _extract_text(raw_output, r"Title:\s*(.+?)(?:\n|$)")
    summary = _extract_text(raw_output, r"Summary:\s*(.+)(?:\n\n|\Z)")

    return title, summary
