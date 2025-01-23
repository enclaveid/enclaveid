from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.local_llm_config import LocalLlmConfig
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

llama8b_config = LlmConfig(
    colloquial_model_name="llama8b",
    local_llm_config=LocalLlmConfig(
        model_name="meta-llama/Meta-Llama-3.1-8B-Instruct",
        sampling_params_args={
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens": 1024,
        },
        vllm_args={
            "tensor_parallel_size": 1,
        },
    ),
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("DEEPINFRA_API_KEY"),
        concurrency_limit=200,
        timeout=60 * 5,
        inference_url="https://api.deepinfra.com/v1/openai/chat/completions",
        inference_config={"model": "meta-llama/Meta-Llama-3.1-8B-Instruct"},
        input_cpm=0.03 / 1000,
        output_cpm=0.05 / 1000,
        context_length=128_000,
    ),
)


def create_llama8b_resource() -> BaseLlmResource:
    return create_llm_resource(llama8b_config)
