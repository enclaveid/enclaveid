from dagster import EnvVar

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

llama405b_config = LlmConfig(
    colloquial_model_name="llama405b",
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_AI_LLAMA405B_API_KEY"),
        concurrency_limit=60,
        timeout=360 * 10,
        inference_url="https://Meta-Llama-3-1-405B-Instruct-snx.eastus2.models.ai.azure.com/v1/chat/completions",
        inference_config={
            "max_tokens": 2048,
            "temperature": 1,
            "top_p": 0.5,
            "best_of": 1,
            "presence_penalty": 0,
            "use_beam_search": "false",
            "ignore_eos": "false",
            "skip_special_tokens": "false",
            "stream": False,
        },
        input_cpm=0.00533,
        output_cpm=0.016,
        context_length=128000,
    ),
)


def create_llama405b_resource() -> BaseLlmResource:
    return create_llm_resource(llama405b_config)
