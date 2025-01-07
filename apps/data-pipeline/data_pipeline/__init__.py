from dagster import (
    Definitions,
    load_assets_from_modules,
    multi_or_in_process_executor,
)

from data_pipeline import assets
from data_pipeline.sensors.inputs_sensor import inputs_sensor
from data_pipeline.sensors.outputs_sensor import outputs_sensor

from .resources import resources

all_assets = load_assets_from_modules(
    [
        assets,
    ]
)


defs = Definitions(
    assets=all_assets,
    sensors=[inputs_sensor, outputs_sensor],
    resources=resources,
    executor=(multi_or_in_process_executor),
)
