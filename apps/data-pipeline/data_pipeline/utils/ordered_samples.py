from numpy.random import default_rng


def ordered_samples(items: list, max_samples: int):
    """
    Samples items from the list, ensuring that the order is maintained.
    """
    if len(items) <= max_samples:
        return items
    else:
        return [
            items[i]
            for i in sorted(
                default_rng().choice(range(len(items)), max_samples, replace=False)
            )
        ]
