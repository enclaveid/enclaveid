import requests
from dagster import (
    HookContext,
    success_hook,
)


@success_hook
def notify_api_on_success(context: HookContext):
    context.log.info(context.op.tags)
    context.log.info(context.op)
    if context.op.tags.get("hook") == "notify_api_on_success":
        response = requests.post(
            "https://api.enclaveid.com/webhooks/pipeline-finished",
            json={"userId": context._step_execution_context.partition_key},
        )
        context.log.info(
            f"Notified API on success for {context._step_execution_context.partition_key}: {response.text}",
        )
