from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import (
    LlmConfig,
    create_llm_resource,
)
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig
from data_pipeline.resources.batch_inference.utils import test_remote_llm_call

_deepseek_config = RemoteLlmConfig(
    api_key=EnvVar("DEEPSEEK_API_KEY"),
    concurrency_limit=50,
    timeout=60 * 10,
    inference_url="https://api.deepseek.com/chat/completions",
    inference_config={
        "model": "deepseek-chat",
        "max_tokens": 8192,
    },
    input_cpm=0.27 / 1000,
    output_cpm=1.1 / 1000,
    context_length=16_000,
)


_deepinfra_config = RemoteLlmConfig(
    api_key=EnvVar("DEEPINFRA_API_KEY"),
    concurrency_limit=200,
    timeout=60 * 5,
    inference_url="https://api.deepinfra.com/v1/openai/chat/completions",
    inference_config={
        "model": "deepseek-ai/DeepSeek-R1",
        "max_tokens": 8192,
    },
    input_cpm=0.85 / 1000,
    output_cpm=0.9 / 1000,
    context_length=16_000,
)

_openrouter_config = RemoteLlmConfig(
    api_key=EnvVar("OPENROUTER_API_KEY"),
    inference_url="https://openrouter.ai/api/v1/chat/completions",
    inference_config={
        "model": "deepseek/deepseek-chat",
        "max_tokens": 8192,
    },
    context_length=16_000,
    concurrency_limit=50,
    timeout=300,
    # In reality these vary by provider but 1$ is a good ballpark
    input_cpm=1 / 1000,
    output_cpm=1 / 1000,
)


v3_config = LlmConfig(
    colloquial_model_name="deepseek_v3",
    remote_llm_config=_deepinfra_config,
)


def create_deepseek_v3_resource() -> BaseLlmResource:
    return create_llm_resource(v3_config)


if __name__ == "__main__":
    test_remote_llm_call(v3_config, "DEEPSEEK_API_KEY")
