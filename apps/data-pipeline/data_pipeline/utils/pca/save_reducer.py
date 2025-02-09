import joblib
from dagster import AssetExecutionContext

from data_pipeline.utils.get_working_dir import get_working_dir


def save_reducer(reducer, context: AssetExecutionContext):
    initiator_phone_number = context.partition_keys[0].split("|")[0]
    partner_phone_number = context.partition_keys[0].split("|")[1]

    working_dir = get_working_dir(context)
    (working_dir / initiator_phone_number).mkdir(parents=True, exist_ok=True)
    joblib.dump(
        reducer,
        working_dir / initiator_phone_number / f"{partner_phone_number}.reducer.joblib",
    )
