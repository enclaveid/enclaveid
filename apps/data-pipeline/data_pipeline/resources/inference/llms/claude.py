from dagster import EnvVar

from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.inference.llm_factory import create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

openrouter_config = RemoteLlmConfig(
    api_key=EnvVar("OPENROUTER_API_KEY"),
    inference_url="https://openrouter.ai/api/v1/chat/completions",
    inference_config={
        "model": "anthropic/claude-3.5-sonnet",  # nb: different from config above
    },
    context_length=200_000,
    concurrency_limit=10,
    timeout=300,
    input_cpm=3 / 1000,
    output_cpm=15 / 1000,
)

claude_config = LlmConfig(
    colloquial_model_name="claude",
    remote_llm_config=openrouter_config,
)


def claude_resource() -> BaseLlmResource:
    return create_llm_resource(claude_config)
