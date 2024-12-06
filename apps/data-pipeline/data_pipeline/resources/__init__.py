from dagster import EnvVar
from dagster_polars import PolarsParquetIOManager
from dagster_ray.kuberay.client import RayJobClient
from dagster_ray.kuberay.configs import in_k8s
from dagster_ray.kuberay.pipes import PipesKubeRayJobClient

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.resources.api_db_session import ApiDbSession
from data_pipeline.resources.embeddings.bge_m3_resource import BGEM3Resource
from data_pipeline.resources.embeddings.nvembed_resource import (
    NVEmbedResource,
)
from data_pipeline.resources.inference.image_generator_resource import (
    ImageGeneratorResource,
)
from data_pipeline.resources.inference.llms.gemini_flash import gemini_flash_resource
from data_pipeline.resources.inference.llms.gemini_pro import gemini_pro_resource
from data_pipeline.resources.inference.llms.gemma9b import create_gemma9b_resource
from data_pipeline.resources.inference.llms.gemma27b import create_gemma27b_resource
from data_pipeline.resources.inference.llms.gpt4o import (
    create_gpt4o_resource,
)
from data_pipeline.resources.inference.llms.gpt4o_mini import create_gpt4o_mini_resource
from data_pipeline.resources.inference.llms.llama8b import create_llama8b_resource
from data_pipeline.resources.inference.llms.llama70b import create_llama70b_resource
from data_pipeline.resources.inference.llms.llama70b_nemotron import (
    create_llama70b_nemotron_resource,
)
from data_pipeline.resources.inference.llms.llama70b_quantized import (
    create_llama70b_quantized_resource,
)
from data_pipeline.resources.inference.llms.llama405b import (
    create_llama405b_resource,
)
from data_pipeline.resources.inference.llms.mistral22b import create_mistral22b_resource
from data_pipeline.resources.inference.llms.mistral_nemo import (
    create_mistral_nemo_resource,
)
from data_pipeline.resources.inference.llms.qwen32b import create_qwen32b_resource

resources = {
    "api_db": ApiDbSession(conn_string=EnvVar("API_DATABASE_URL")),
    "nvembed": NVEmbedResource(),
    "bge_m3": BGEM3Resource(api_key=EnvVar("DEEPINFRA_API_KEY")),
    "gemma27b": create_gemma27b_resource(),
    "gemma9b": create_gemma9b_resource(),
    "gemini_flash": gemini_flash_resource(),
    "gemini_pro": gemini_pro_resource(),
    "gpt4o": create_gpt4o_resource(),
    "gpt4o_mini": create_gpt4o_mini_resource(),
    "image_generator": ImageGeneratorResource(),
    "llama405b": create_llama405b_resource(),
    "llama70b": create_llama70b_resource(),
    "llama70b_nemotron": create_llama70b_nemotron_resource(),
    "llama70b_quantized": create_llama70b_quantized_resource(),
    "llama8b": create_llama8b_resource(),
    "mistral22b": create_mistral22b_resource(),
    "mistral_nemo": create_mistral_nemo_resource(),
    "parquet_io_manager": PolarsParquetIOManager(
        extension=".snappy", base_dir=str(DAGSTER_STORAGE_BUCKET)
    ),
    "qwen32b": create_qwen32b_resource(),
    "pipes_kube_rayjob_client": PipesKubeRayJobClient(
        client=RayJobClient(
            config_file="/Users/ma9o/.kube/config",
            context="enclaveid-cluster-prod",
        )
        if not in_k8s
        else None,
        port_forward=not in_k8s,
    ),
}
