import polars as pl
from ai_agents.base_agent import TraceRecord
from dagster import AssetExecutionContext

from data_pipeline.utils.get_working_dir import get_working_dir


def save_agent_traces(traces: list[TraceRecord], context: AssetExecutionContext):
    working_dir = get_working_dir(context)
    working_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(traces).write_parquet(
        f"{working_dir}/{context.partition_key}.traces.snappy"
    )
