import ast

import requests
from dagster import (
    DefaultSensorStatus,
    SensorEvaluationContext,
    SensorResult,
    SkipReason,
    sensor,
)
from upath import UPath

from data_pipeline.constants.environments import STORAGE_BUCKET, get_environment


@sensor(
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.STOPPED
    if get_environment() == "LOCAL"
    else DefaultSensorStatus.RUNNING,
)
def outputs_sensor(context: SensorEvaluationContext) -> SensorResult | SkipReason:
    """Notifies the API that a pipeline has finished."""

    current_state: set = ast.literal_eval(context.cursor) if context.cursor else set()  # type: ignore
    asset_folder: UPath = STORAGE_BUCKET / "results_for_api"

    asset_folder.fs.invalidate_cache()
    all_partitions = {d.stem for d in asset_folder.iterdir() if d.is_file()}

    partitions_to_add = all_partitions - current_state
    # TODO: partitions_to_delete = current_state - all_partitions

    results = list(
        map(
            lambda user_id: requests.post(
                "https://api.enclaveid.com/webhooks/pipeline-finished",
                json={"userId": user_id},
                timeout=60 * 2,  # TODO: azure psql slow af
            ).json(),
            partitions_to_add,
        )
    )

    context.log.info(partitions_to_add)
    context.log.info(results)

    errored_partitions = set(
        [
            item
            for item, result in zip(partitions_to_add, results)
            if not result.get("success")
        ]
    )

    new_cursor = all_partitions - errored_partitions

    return SensorResult([], cursor=str(new_cursor))
