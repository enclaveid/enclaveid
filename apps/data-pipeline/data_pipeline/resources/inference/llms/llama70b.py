from dagster import EnvVar

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

llama70b_config = LlmConfig(
    colloquial_model_name="llama70b",
    local_llm_config=LocalLlmConfig(
        model_name="meta-llama/Llama-3.1-70B-Instruct",
        sampling_params_args={
            "max_tokens": 2048,
        },
        vllm_args={
            # "max_model_len": 1024 * 80,
            "tensor_parallel_size": 4,
        },
    ),
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_AI_LLAMA70B_API_KEY"),
        concurrency_limit=60,
        timeout=60,
        inference_url="https://Meta-Llama-3-70B-Instruct-pbssd-serverless.eastus2.inference.ai.azure.com/v1/chat/completions",
        inference_config={
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 0.5,
            "best_of": 1,
            "presence_penalty": 0,
            "use_beam_search": "false",
            "ignore_eos": "false",
            "skip_special_tokens": "false",
            "stream": False,
        },
        input_cpm=0.00268,
        output_cpm=0.00354,
        context_length=128000,
    ),
)


def create_llama70b_resource() -> BaseLlmResource:
    return create_llm_resource(llama70b_config)
