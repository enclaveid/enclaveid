from abc import ABC, abstractmethod

import polars as pl
from dagster import ConfigurableResource


class BaseEmbedderResource(ConfigurableResource, ABC):
    @abstractmethod
    def get_embeddings(self, series: pl.Series) -> tuple[pl.Series, float]:
        """
        Given the input series of strings, returns a tuple of the embeddings and the cost of the inference.
        """
        pass
