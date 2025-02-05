def get_node_datetime(datetimes: list[str]) -> str:
    # Remove nulls and duplicates
    datetimes = [d for d in datetimes if d is not None]
    datetimes = list(set(datetimes))

    if len(datetimes) == 0:
        return "Unknown"

    if len(datetimes) == 1:
        return datetimes[0]
    else:
        sorted_datetimes = sorted(datetimes)
        return f"from {sorted_datetimes[0]} to {sorted_datetimes[-1]}"
