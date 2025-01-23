from dagster import EnvVar
from dagster_polars import PolarsParquetIOManager

from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.resources.batch_embedder import BatchEmbedderResource
from data_pipeline.resources.batch_inference.llms.claude import claude_resource
from data_pipeline.resources.batch_inference.llms.gemini_pro import gemini_pro_resource
from data_pipeline.resources.batch_inference.llms.gpt4o import create_gpt4o_resource
from data_pipeline.resources.batch_inference.llms.gpt4o_mini import create_gpt4o_mini_resource
from data_pipeline.resources.batch_inference.llms.llama8b import create_llama8b_resource
from data_pipeline.resources.batch_inference.llms.llama70b import create_llama70b_resource
from data_pipeline.resources.batch_inference.llms.llama70b_turbo import (
    create_llama70b_turbo_resource,
)

resources = {
    "batch_embedder": BatchEmbedderResource(base_url=EnvVar("RAY_APP_ADDRESS")),
    "claude": claude_resource(),
    "llama70b_turbo": create_llama70b_turbo_resource(),
    "llama70b": create_llama70b_resource(),
    "llama8b": create_llama8b_resource(),
    "gemini_pro": gemini_pro_resource(),
    "gpt4o": create_gpt4o_resource(),
    "gpt4o_mini": create_gpt4o_mini_resource(),
    "parquet_io_manager": PolarsParquetIOManager(
        extension=".snappy", base_dir=str(DAGSTER_STORAGE_DIRECTORY)
    ),
}
