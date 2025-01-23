from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

llama70b_config = LlmConfig(
    colloquial_model_name="llama70b",
    remote_llm_config=RemoteLlmConfig(
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
        input_cpm=0.00071,
        output_cpm=0.00071,
        context_length=128000,
    ),
)


def create_llama70b_resource() -> BaseLlmResource:
    return create_llm_resource(llama70b_config)
