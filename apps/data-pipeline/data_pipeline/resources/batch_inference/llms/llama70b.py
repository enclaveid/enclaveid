from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import (
    LlmConfig,
    create_llm_resource,
)
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

_azure_config = RemoteLlmConfig(
    api_key=EnvVar("AZURE_AI_LLAMA70B_API_KEY"),
    concurrency_limit=100,
    timeout=60 * 10,
    inference_url="https://Llama-3-3-70B-Instruct-txfwk.eastus2.models.ai.azure.com/v1/chat/completions",
    inference_config={
        "max_tokens": 2048,
        "temperature": 0.8,
        "top_p": 0.1,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        # "best_of": 1,
        # "use_beam_search": "false",
        # "ignore_eos": "false",
        # "skip_special_tokens": "false",
        # "stream": False,
    },
    input_cpm=0.71,
    output_cpm=0.71,
    context_length=128000,
)

_deepinfra_config = RemoteLlmConfig(
    api_key=EnvVar("DEEPINFRA_API_KEY"),
    concurrency_limit=200,
    timeout=60 * 5,
    inference_url="https://api.deepinfra.com/v1/openai/chat/completions",
    inference_config={"model": "meta-llama/Llama-3.3-70B-Instruct"},
    input_cpm=0.23,
    output_cpm=0.4,
    context_length=128_000,
)

llama70b_config = LlmConfig(
    colloquial_model_name="llama70b",
    remote_llm_config=_deepinfra_config,
)


def create_llama70b_resource() -> BaseLlmResource:
    return create_llm_resource(llama70b_config)
