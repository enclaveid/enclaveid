import polars as pl


def _get_missing_time_expr(col: str) -> pl.Expr:
    return (
        pl.col(col).is_not_null()
        & pl.col(col)
        .str.strptime(pl.Time, format="%H:%M:%S", strict=False, ambiguous="null")
        .is_not_null()
    )


# Helper expressions to check if a time is missing (either null or NaN)
_start_time_missing = _get_missing_time_expr("start_time")
_end_time_missing = _get_missing_time_expr("end_time")

_same_date = pl.col("start_date") == pl.col("end_date")
_diff_date = pl.col("start_date") != pl.col("end_date")

_both_times_missing = _start_time_missing & _end_time_missing
_both_times_present = ~_start_time_missing & ~_end_time_missing
_partial_times = ~_both_times_missing & ~_both_times_present  # exactly one is missing


relevance_period_expr = (
    pl.when(
        # 1) Same date, both times missing
        _same_date & _both_times_missing
    )
    .then(
        pl.col("start_date").cast(pl.Utf8)  # e.g. "2024-12-21"
    )
    .when(
        # 2) Same date, both times present and different
        _same_date & _both_times_present & (pl.col("start_time") != pl.col("end_time"))
    )
    .then(
        # e.g. "2024-12-21 from 09:00 to 17:00"
        pl.format(
            "{} from {} to {}",
            pl.col("start_date").cast(pl.Utf8),
            pl.col("start_time").cast(pl.Utf8),
            pl.col("end_time").cast(pl.Utf8),
        )
    )
    .when(
        # 3) Same date, both times present but equal
        _same_date & _both_times_present & (pl.col("start_time") == pl.col("end_time"))
    )
    .then(
        # e.g. "2024-12-21 at 09:00"
        pl.format(
            "{} at {}",
            pl.col("start_date").cast(pl.Utf8),
            pl.col("start_time").cast(pl.Utf8),
        )
    )
    .when(
        # 4) Same date, partial times (exactly one present)
        _same_date & _partial_times
    )
    .then(
        # e.g. "2024-12-21 at 09:00" (if only start_time is present)
        # or "2024-12-21 at 17:00" (if only end_time is present)
        pl.when(_start_time_missing & ~_end_time_missing)
        .then(
            # only end_time is present
            pl.format(
                "{} at {}",
                pl.col("start_date").cast(pl.Utf8),
                pl.col("end_time").cast(pl.Utf8),
            )
        )
        .otherwise(
            # only start_time is present
            pl.format(
                "{} at {}",
                pl.col("start_date").cast(pl.Utf8),
                pl.col("start_time").cast(pl.Utf8),
            )
        )
    )
    .when(
        # 5) Different dates, both times missing
        _diff_date & _both_times_missing
    )
    .then(
        # e.g. "2024-12-21 to 2024-12-22"
        pl.format(
            "{} to {}",
            pl.col("start_date").cast(pl.Utf8),
            pl.col("end_date").cast(pl.Utf8),
        )
    )
    .when(
        # 6) Different dates, both times present
        _diff_date & _both_times_present
    )
    .then(
        # e.g. "2024-12-21 at 09:00 to 2024-12-22 at 17:00"
        pl.format(
            "{} at {} to {} at {}",
            pl.col("start_date").cast(pl.Utf8),
            pl.col("start_time").cast(pl.Utf8),
            pl.col("end_date").cast(pl.Utf8),
            pl.col("end_time").cast(pl.Utf8),
        )
    )
    .when(
        # 7) Different dates, partial times
        _diff_date & _partial_times
    )
    .then(
        # We have two sub-cases here:
        #   - Start time missing, end time present => "start_date to end_date at end_time"
        #   - Start time present, end time missing => "start_date at start_time to end_date"
        pl.when(_start_time_missing & ~_end_time_missing)
        .then(
            # e.g. "2024-12-21 to 2024-12-22 at 17:00"
            pl.format(
                "{} to {} at {}",
                pl.col("start_date").cast(pl.Utf8),
                pl.col("end_date").cast(pl.Utf8),
                pl.col("end_time").cast(pl.Utf8),
            )
        )
        .otherwise(
            # e.g. "2024-12-21 at 09:00 to 2024-12-22"
            pl.format(
                "{} at {} to {}",
                pl.col("start_date").cast(pl.Utf8),
                pl.col("start_time").cast(pl.Utf8),
                pl.col("end_date").cast(pl.Utf8),
            )
        )
    )
    .otherwise(
        # 8) Fallback / undefined scenario
        pl.lit("Undefined scenario")
    )
    .alias("relevance_period")
)
