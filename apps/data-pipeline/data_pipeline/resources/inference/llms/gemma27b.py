from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig

gemma27b_config = LlmConfig(
    colloquial_model_name="gemma27b",
    local_llm_config=LocalLlmConfig(
        model_name="google/gemma-2-27b-it",
        sampling_params_args={
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 1024,
        },
        vllm_args={
            "enforce_eager": True,
            "tensor_parallel_size": 2,
        },
    ),
)


def create_gemma27b_resource() -> BaseLlmResource:
    return create_llm_resource(gemma27b_config)
