from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.local_llm_config import LocalLlmConfig

llama70b_quantized_config = LlmConfig(
    colloquial_model_name="llama70b_quantized",
    local_llm_config=LocalLlmConfig(
        model_name="neuralmagic/Meta-Llama-3.1-70B-Instruct-quantized.w8a16",
        sampling_params_args={
            "temperature": 0.6,
            "top_p": 0.3,
            "max_tokens": 1024,
        },
        vllm_args={
            # We use 80k instead of the default 128k to avoid OOM errors
            "max_model_len": 1024 * 80,
            "tensor_parallel_size": 2,
        },
    ),
)


def create_llama70b_quantized_resource() -> BaseLlmResource:
    return create_llm_resource(llama70b_quantized_config)
