import joblib
from dagster import AssetExecutionContext

from data_pipeline.utils.get_working_dir import get_working_dir


def save_reducer(reducer, context: AssetExecutionContext):
    working_dir = get_working_dir(context)
    working_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(reducer, working_dir / f"{context.partition_key}.reducer.joblib")
