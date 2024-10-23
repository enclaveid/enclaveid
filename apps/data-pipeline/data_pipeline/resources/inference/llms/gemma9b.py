from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig

gemma9b_config = LlmConfig(
    colloquial_model_name="gemma9b",
    local_llm_config=LocalLlmConfig(
        model_name="google/gemma-2-9b-it",
        sampling_params_args={
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 1024,
        },
        vllm_args={
            "enforce_eager": True,
            "tensor_parallel_size": 1,
        },
    ),
)


def create_gemma9b_resource() -> BaseLlmResource:
    return create_llm_resource(gemma9b_config)
