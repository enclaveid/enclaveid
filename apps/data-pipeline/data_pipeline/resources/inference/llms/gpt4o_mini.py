from dagster import EnvVar

from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.inference.llm_factory import create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

gpt4o_mini_config = LlmConfig(
    colloquial_model_name="gpt-4o-mini",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_AI_GPT4O_MINI_API_KEY"),
        concurrency_limit=100,
        timeout=60 * 10,
        inference_url="https://enclaveidai2163546968.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-08-01-preview",
        inference_config={
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "model": "gpt-4o-mini",
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=0.15 / 1000,
        output_cpm=0.6 / 1000,
        context_length=128_000,
    ),
)


def create_gpt4o_mini_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4o_mini_config)
