from dagster import (
    Definitions,
    load_assets_from_modules,
    multi_or_in_process_executor,
)
from dagster_k8s import k8s_job_executor

from data_pipeline.consts import get_environment

from .assets import old_history, takeout
from .resources import resources
from .sensors import users_sensor

all_assets = load_assets_from_modules(
    [
        takeout,
        old_history,
        # recent_history,  TODO: Uncomment this line to enable the recent_history asset
    ]
)

defs = Definitions(
    assets=all_assets,
    sensors=[users_sensor],
    resources=resources,
    executor=(
        k8s_job_executor
        if get_environment() != "LOCAL"
        else multi_or_in_process_executor
    ),
)
