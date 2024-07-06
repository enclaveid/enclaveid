from dagster import EnvVar
from dagster_polars import PolarsParquetIOManager

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.llm_inference.gpt4_resource import Gpt4Resource
from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource
from data_pipeline.resources.llm_inference.llama70b_resource import Llama70bResource
from data_pipeline.resources.mistral_resource import MistralResource
from data_pipeline.resources.postgres_resource import PGVectorClientResource

resources = {
    "parquet_io_manager": PolarsParquetIOManager(
        extension=".snappy", base_dir=str(DAGSTER_STORAGE_BUCKET)
    ),
    "mistral": MistralResource(api_key=EnvVar("MISTRAL_API_KEY")),
    # TODO: use a single env var with the uri
    "pgvector": PGVectorClientResource(
        host=EnvVar("PGHOST"),
        port=EnvVar.int("PGPORT"),
        user=EnvVar("PGUSER"),
        password=EnvVar("PGPASSWORD"),
        dbname=EnvVar("PGDATABASE"),
    ),
    "llama8b": Llama8bResource(),
    "llama70b": Llama70bResource(api_key=EnvVar("AZURE_AI_LLAMA70B_API_KEY")),
    "gpt4": Gpt4Resource(api_key=EnvVar("AZURE_AI_GPT4_API_KEY")),
}
