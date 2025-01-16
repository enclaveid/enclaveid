from typing import Any

from dagster import (
    Definitions,
    load_assets_from_modules,
    multi_or_in_process_executor,
)

from data_pipeline import assets
from data_pipeline.assets import human_conversations
from data_pipeline.assets.ai_conversations import graph, plain
from data_pipeline.sensors.inputs_sensor import inputs_sensor
from data_pipeline.sensors.outputs_sensor import outputs_sensor
from data_pipeline.utils.feature_flags import (
    IS_AI_CONVERSATIONS_ENABLED,
    IS_CAUSAL_GRAPH_ENABLED,
    IS_HUMAN_CONVERSATIONS_ENABLED,
)

from .resources import resources

asset_modules: list[Any] = [assets]

if IS_AI_CONVERSATIONS_ENABLED:
    if IS_CAUSAL_GRAPH_ENABLED:
        asset_modules.append(graph)
    else:
        asset_modules.append(plain)

if IS_HUMAN_CONVERSATIONS_ENABLED:
    asset_modules.append(human_conversations)

all_assets = load_assets_from_modules(asset_modules)


defs = Definitions(
    assets=all_assets,
    sensors=[inputs_sensor, outputs_sensor],
    resources=resources,
    executor=(multi_or_in_process_executor),
)
