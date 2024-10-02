from dagster import EnvVar
from dagster_polars import PolarsParquetIOManager

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.api_db_session import ApiDbSession
from data_pipeline.resources.inference.gpt4_resource import Gpt4Resource
from data_pipeline.resources.inference.image_generator_resource import (
    ImageGeneratorResource,
)
from data_pipeline.resources.inference.llama70b_resource import Llama70bResource
from data_pipeline.resources.inference.llama405b_resource import Llama405bResource
from data_pipeline.resources.inference.local_llms.gemma9b_resource import (
    Gemma9bResource,
)
from data_pipeline.resources.inference.local_llms.gemma27b_resource import (
    Gemma27bResource,
)
from data_pipeline.resources.inference.local_llms.llama8b_resource import (
    Llama8bResource,
)
from data_pipeline.resources.inference.local_llms.llama70b_bf16_resource import (
    Llama70bBf16Resource,
)
from data_pipeline.resources.inference.local_llms.llama70b_quantized_resource import (
    Llama70bQuantizedResource,
)
from data_pipeline.resources.inference.local_llms.mistral22b_resource import (
    Mistral22bResource,
)
from data_pipeline.resources.inference.local_llms.mistral_nemo_resource import (
    MistralNemoResource,
)
from data_pipeline.resources.mistral_resource import MistralResource
from data_pipeline.resources.sentence_transfomer_resource import (
    SentenceTransformerResource,
)

resources = {
    "parquet_io_manager": PolarsParquetIOManager(
        extension=".snappy", base_dir=str(DAGSTER_STORAGE_BUCKET)
    ),
    "mistral": MistralResource(api_key=EnvVar("MISTRAL_API_KEY")),
    "api_db": ApiDbSession(conn_string=EnvVar("API_DATABASE_URL")),
    "mistral_nemo": MistralNemoResource(),
    "mistral22b": Mistral22bResource(),
    "gemma27b": Gemma27bResource(),
    "llama8b": Llama8bResource(),
    "gemma9b": Gemma9bResource(),
    "llama70b": Llama70bResource(api_key=EnvVar("AZURE_AI_LLAMA70B_API_KEY")),
    "llama70b_quantized": Llama70bQuantizedResource(),
    "llama70b_bf16": Llama70bBf16Resource(),
    "llama405b": Llama405bResource(api_key=EnvVar("AZURE_AI_LLAMA405B_API_KEY")),
    "gpt4": Gpt4Resource(api_key=EnvVar("AZURE_AI_GPT4_API_KEY")),
    "embedding_model": SentenceTransformerResource(),
    "image_generator": ImageGeneratorResource(),
}
