import logging

from dagster import AssetExecutionContext, InitResourceContext


def get_logger(context: InitResourceContext | AssetExecutionContext):
    """Get the Dagster logger for the given context or fallback to Python logging."""
    return (
        context.log
        if (context and (hasattr(context, "log") and context.log))
        else (logging.basicConfig(level=logging.INFO) or logging.getLogger(__name__))
    )
