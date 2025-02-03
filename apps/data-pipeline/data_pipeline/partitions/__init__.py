import os

from dagster import (
    DagsterInstance,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
)

from data_pipeline.constants.environments import get_environment

user_partitions_def = DynamicPartitionsDefinition(name="users")

phone_number_partitions_def = DynamicPartitionsDefinition(name="phone_numbers")

multi_phone_number_partitions_def = MultiPartitionsDefinition(
    {
        "phone_number1": phone_number_partitions_def,
        "phone_number2": phone_number_partitions_def,
    }
)

# Add test user to dev instance
if get_environment() == "LOCAL":
    instance = DagsterInstance.get()
    instance.add_dynamic_partitions(
        partitions_def_name=phone_number_partitions_def.name,
        partition_keys=[
            os.getenv("TEST_PHONE_NUMBER_1"),
            os.getenv("TEST_PHONE_NUMBER_2"),
        ],
    )
