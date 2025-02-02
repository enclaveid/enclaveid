from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import (
    LlmConfig,
    create_llm_resource,
)
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

o1_mini_config = LlmConfig(
    colloquial_model_name="o1-mini",
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_OPENAI_API_KEY"),
        concurrency_limit=100,
        timeout=60 * 10,
        inference_url="https://enclaveidai2163546968.openai.azure.com/openai/deployments/o1-mini/chat/completions?api-version=2024-08-01-preview",
        inference_config={
            "model": "o1-mini",
        },
        input_cpm=3,
        output_cpm=12,
        context_length=128_000,
    ),
)


def create_o1_mini_resource() -> BaseLlmResource:
    return create_llm_resource(o1_mini_config)
