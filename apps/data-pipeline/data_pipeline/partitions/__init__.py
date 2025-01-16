from dagster import DagsterInstance, DynamicPartitionsDefinition

from data_pipeline.constants.environments import get_environment

# TODO: why would we want to name them differently wtf
user_partitions_def = DynamicPartitionsDefinition(name="users")

# Add test user to dev instance
if get_environment() == "LOCAL":
    instance = DagsterInstance.get()
    instance.add_dynamic_partitions(
        user_partitions_def.name, ["cm0i27jdj0000aqpa73ghpcxf"]
    )
