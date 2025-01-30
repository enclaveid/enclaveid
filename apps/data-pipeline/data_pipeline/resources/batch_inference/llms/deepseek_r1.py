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
    concurrency_limit=100,
    timeout=60 * 10,
    inference_url="https://api.deepseek.com/chat/completions",
    inference_config={
        "model": "deepseek-reasoner",
        "max_tokens": 8192,
    },
    input_cpm=0.55 / 1000,
    output_cpm=2.19 / 1000,
    context_length=64_000,
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
    output_cpm=2.5 / 1000,
    context_length=64_000,
)

_openrouter_config = RemoteLlmConfig(
    api_key=EnvVar("OPENROUTER_API_KEY"),
    inference_url="https://openrouter.ai/api/v1/chat/completions",
    inference_config={
        "model": "deepseek/deepseek-r1",
    },
    context_length=64_000,
    concurrency_limit=50,
    timeout=300,
    # In reality these vary by provider but 4$ is a good ballpark
    input_cpm=4 / 1000,
    output_cpm=4 / 1000,
    provider={
        "order": [
            "Novita",
            "Avian",
            "DeepInfra",
        ],
    },
)

_azure_config = RemoteLlmConfig(
    api_key=EnvVar("DEEPSEEK_AZURE_API_KEY"),
    concurrency_limit=10,
    timeout=60 * 10,
    inference_url="https://DeepSeek-R1-ozcav.eastus2.models.ai.azure.com/v1/chat/completions",
    inference_config={
        "model": "deepseek-reasoner",
        "max_tokens": 8192,
    },
    input_cpm=0.55 / 1000,
    output_cpm=2.19 / 1000,
    context_length=16_000,
)

r1_config = LlmConfig(
    colloquial_model_name="deepseek_r1",
    remote_llm_config=_deepinfra_config,
)


def create_deepseek_r1_resource() -> BaseLlmResource:
    return create_llm_resource(r1_config)


if __name__ == "__main__":
    test_remote_llm_call(r1_config, "OPENROUTER_API_KEY")
