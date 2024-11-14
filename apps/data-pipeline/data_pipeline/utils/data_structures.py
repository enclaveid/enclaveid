from typing import Sequence


def flatten(xss: list[list]):
    return [x for xs in xss for x in xs]


def get_dict_leaf_values(d: dict, leaves=None):
    if leaves is None:
        leaves = []

    if isinstance(d, dict):
        for value in d.values():
            get_dict_leaf_values(value, leaves)
    else:
        leaves.append(d)

    return leaves


def deep_merge(dict1: dict, dict2: dict) -> dict:
    merged = dict1.copy()
    for key, value in dict2.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def filter_none(xs: Sequence) -> Sequence:
    return list(filter(lambda x: x is not None, xs))
