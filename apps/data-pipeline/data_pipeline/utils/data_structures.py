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
