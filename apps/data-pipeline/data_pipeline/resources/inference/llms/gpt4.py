from dagster import EnvVar

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

# TODO: Implement batch https://platform.openai.com/docs/api-reference/batch
gpt4_config = LlmConfig(
    colloquial_model_name="gpt-4o-2024-08-06",
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_AI_GPT4_API_KEY"),
        concurrency_limit=256,
        timeout=60 * 10,
        inference_url="https://api.openai.com/v1/chat/completions",
        inference_config={
            "model": "gpt-4o-2024-08-06",
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=2.5 / 1000,
        output_cpm=10 / 1000,
        context_length=128_000,
    ),
)


def create_gpt4_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4_config)
