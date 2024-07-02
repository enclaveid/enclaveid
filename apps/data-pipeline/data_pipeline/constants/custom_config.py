from typing import Optional

from dagster import Config
from pydantic import Field

from ..consts import DEPLOYMENT_ROW_LIMIT


class RowLimitConfig(Config):
    row_limit: Optional[int] = Field(
        default=DEPLOYMENT_ROW_LIMIT,
        description=(
            "Compute results for a subset of the data. Useful for testing "
            "environments."
        ),
    )
