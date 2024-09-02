from dagster import DynamicPartitionsDefinition

# TODO: why would we want to name them differently wtf
user_partitions_def = DynamicPartitionsDefinition(name="users")
