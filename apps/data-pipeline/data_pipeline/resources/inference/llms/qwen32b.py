from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig

qwen32b_config = LlmConfig(
    colloquial_model_name="qwen32b",
    local_llm_config=LocalLlmConfig(
        model_name="Qwen/Qwen2.5-32B-Instruct",
        sampling_params_args={
            "max_tokens": 2048,
        },
        vllm_args={
            "tensor_parallel_size": 2,
        },
    ),
)


def create_qwen32b_resource() -> BaseLlmResource:
    return create_llm_resource(qwen32b_config)
