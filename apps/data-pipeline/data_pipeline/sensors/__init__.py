import ast

from dagster import (
    AssetSelection,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    SkipReason,
    sensor,
)

from ..consts import PRODUCTION_STORAGE_BUCKET, get_environment
from ..partitions import user_partitions_def

SENSOR_INTERVAL_SECONDS = 5 if get_environment() == "LOCAL" else 30


@sensor(
    asset_selection=AssetSelection.all(),
    minimum_interval_seconds=SENSOR_INTERVAL_SECONDS,
)
def users_sensor(context: SensorEvaluationContext) -> SensorResult | SkipReason:
    """Polls the storage bucket for user folders.

    Adds or removes user partitions based on the presence of user folders. Note
    that this will also remove partitions if a user's folder has been deleted."""

    current_state: set = ast.literal_eval(context.cursor) if context.cursor else set()  # type: ignore
    all_dirs = {d.name for d in PRODUCTION_STORAGE_BUCKET.iterdir() if d.is_dir()}

    dirs_to_add = all_dirs - current_state
    dirs_to_delete = current_state - all_dirs

    if len(dirs_to_add) + len(dirs_to_delete) > 0:
        return SensorResult(
            run_requests=[
                RunRequest(
                    run_key=f"first_upload_{k}",
                    partition_key=k,
                )
                for k in dirs_to_add
            ],
            cursor=str(all_dirs),
            dynamic_partitions_requests=[
                user_partitions_def.build_add_request(sorted(dirs_to_add)),
                user_partitions_def.build_delete_request(sorted(dirs_to_delete)),
            ],
        )

    else:
        return SkipReason("No changes detected at the end.")
