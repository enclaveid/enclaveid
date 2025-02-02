from dagster import EnvVar

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.local_llm_config import LocalLlmConfig
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

llama70b_nemotron_config = LlmConfig(
    colloquial_model_name="llama70b_nemotron",
    local_llm_config=LocalLlmConfig(
        model_name="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
        sampling_params_args={
            "max_tokens": 2048,
        },
        vllm_args={
            # "max_model_len": 1024 * 80,
            "tensor_parallel_size": 4,
        },
    ),
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("DEEPINFRA_API_KEY"),
        concurrency_limit=200,
        timeout=60 * 5,
        inference_url="https://api.deepinfra.com/v1/openai/chat/completions",
        inference_config={"model": "nvidia/Llama-3.1-Nemotron-70B-Instruct"},
        input_cpm=0.35,
        output_cpm=0.4,
        context_length=128_000,
    ),
)


def create_llama70b_nemotron_resource() -> BaseLlmResource | None:
    return create_llm_resource(llama70b_nemotron_config)
