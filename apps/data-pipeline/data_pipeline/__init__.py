from dagster import (
    Definitions,
    load_assets_from_modules,
    multi_or_in_process_executor,
)
from dagster_k8s import k8s_job_executor

from data_pipeline.consts import get_environment
from data_pipeline.sensors.inputs_sensor import inputs_sensor
from data_pipeline.sensors.outputs_sensor import outputs_sensor

from .assets import search_history, takeout
from .resources import resources

all_assets = load_assets_from_modules(
    [
        takeout,
        search_history,
        # recent_history,  TODO: Uncomment this line to enable the recent_history asset
    ]
)


defs = Definitions(
    assets=all_assets,
    sensors=[inputs_sensor, outputs_sensor],
    resources=resources,
    executor=(
        k8s_job_executor
        if get_environment() != "LOCAL"
        else multi_or_in_process_executor
    ),
)
