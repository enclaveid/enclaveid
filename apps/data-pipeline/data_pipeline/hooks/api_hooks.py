import requests
from dagster import (
    HookContext,
    success_hook,
)


@success_hook(name="notify_api_on_success")
def notify_api_on_success(context: HookContext):
    if context.op.tags.get("hook") == "notify_api_on_success":
        requests.post(
            "https://api.enclaveid.com/webhooks/pipeline-finished",
            json={"userId": context._step_execution_context.partition_key},
        )
