from upath import UPath

from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY


def get_working_dir(context) -> UPath:
    return DAGSTER_STORAGE_DIRECTORY / UPath(context.asset_key.path[-1])
