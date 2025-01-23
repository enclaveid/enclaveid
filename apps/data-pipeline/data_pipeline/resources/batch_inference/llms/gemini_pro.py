from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.batch_inference.llm_factory import create_llm_resource
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

openrouter_config = RemoteLlmConfig(
    api_key=EnvVar("OPENROUTER_API_KEY"),
    inference_url="https://openrouter.ai/api/v1/chat/completions",
    inference_config={
        "model": "google/gemini-pro-1.5",  # nb: different from config above
    },
    context_length=1_000_000,
    concurrency_limit=200,
    timeout=300,
    input_cpm=1.25 / 1000,
    output_cpm=5 / 1000,
)

gemini_pro_config = LlmConfig(
    colloquial_model_name="gemini_pro",
    remote_llm_config=openrouter_config,
)


def gemini_pro_resource() -> BaseLlmResource:
    return create_llm_resource(gemini_pro_config)
