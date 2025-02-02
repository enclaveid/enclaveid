from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import (
    LlmConfig,
    create_llm_resource,
)
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

# TODO: Implement batch https://platform.openai.com/docs/api-reference/batch
gpt4o_config = LlmConfig(
    colloquial_model_name="gpt-4o",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_OPENAI_API_KEY"),
        concurrency_limit=32,
        timeout=60 * 10,
        inference_url="https://enclaveidai2163546968.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview",
        inference_config={
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "model": "gpt-4o",
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=2.5,
        output_cpm=10,
        context_length=128_000,
    ),
)


def create_gpt4o_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4o_config)
