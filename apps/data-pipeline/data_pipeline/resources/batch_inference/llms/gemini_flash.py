from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.batch_inference.llm_factory import create_llm_resource
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

# TODO: Fix rate limits
vertex_ai_config = RemoteLlmConfig(
    api_key=EnvVar("GEMINI_API_KEY"),
    inference_url="https://us-central1-aiplatform.googleapis.com/v1beta1/projects/enclaveid/locations/us-central1/endpoints/openapi/chat/completions",
    inference_config={
        "model": "google/gemini-1.5-flash",
        # "temperature": 0.2,
        # "top_p": 0.95,
    },
    context_length=1_000_000,
    concurrency_limit=200,
    timeout=300,
    # This is for prompts under 128k tokens. A token is about 4.5 characters
    # See: https://cloud.google.com/vertex-ai/generative-ai/pricing
    input_cpm=0.01875 * 4.5,
    output_cpm=0.075 * 4.5,
)

openrouter_config = RemoteLlmConfig(
    api_key=EnvVar("OPENROUTER_API_KEY"),
    inference_url="https://openrouter.ai/api/v1/chat/completions",
    inference_config={
        "model": "google/gemini-flash-1.5",  # nb: different from config above
    },
    context_length=1_000_000,
    concurrency_limit=200,
    timeout=300,
    input_cpm=0.3,
    output_cpm=0.3,
)

gemini_flash_config = LlmConfig(
    colloquial_model_name="gemini_flash",
    remote_llm_config=openrouter_config,
)


def gemini_flash_resource() -> BaseLlmResource:
    return create_llm_resource(gemini_flash_config)
