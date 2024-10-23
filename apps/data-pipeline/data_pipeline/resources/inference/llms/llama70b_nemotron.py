from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig

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
)


def create_llama70b_nemotron_resource() -> BaseLlmResource:
    return create_llm_resource(llama70b_nemotron_config)
