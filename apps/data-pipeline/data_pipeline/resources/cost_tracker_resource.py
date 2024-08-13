import datetime

import polars as pl
from dagster import AssetExecutionContext, ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET


class CostTrackerResource(ConfigurableResource):
    _cost_df: pl.DataFrame = PrivateAttr()
    _cost_df_path = DAGSTER_STORAGE_BUCKET / "cost_tracker.snappy"
    _logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        if self._cost_df_path.exists():
            self._cost_df = pl.read_parquet(self._cost_df_path)
        else:
            self._cost_df = pl.DataFrame(
                schema={"partition_id": pl.Utf8, "last_updated": pl.Datetime}
            )
        self._logger = context.log
        return super().setup_for_execution(context)

    def log_cost(self, cost: float, context: AssetExecutionContext) -> None:
        partition_id = context.partition_key
        asset_name = context.asset_key.path[-1]

        self._logger.info(f"Cost for {asset_name} in partition {partition_id}: {cost}")

        # Ensure the asset column exists
        if asset_name not in self._cost_df.columns:
            self._cost_df = self._cost_df.with_columns(
                pl.lit(0).alias(asset_name).cast(pl.Float64)
            )

        # Update or add the cost for the specific asset and partition
        new_row = pl.DataFrame(
            {
                "partition_id": [partition_id],
                "last_updated": [datetime.datetime.now()],
                asset_name: [float(cost)],
            }
        )

        # Only keep the most recent cost for each partition
        self._cost_df = (
            pl.concat([self._cost_df, new_row])
            .sort("last_updated")
            .group_by("partition_id")
            .agg(pl.all().last())
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        self._cost_df.write_parquet(self._cost_df_path)
        return super().teardown_after_execution(context)
