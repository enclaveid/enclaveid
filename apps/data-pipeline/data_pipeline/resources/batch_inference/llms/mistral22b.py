from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.local_llm_config import LocalLlmConfig

mistral22b_config = LlmConfig(
    colloquial_model_name="mistral22b",
    local_llm_config=LocalLlmConfig(
        model_name="mistralai/Mistral-Small-Instruct-2409",
        sampling_params_args={
            "max_tokens": 2048,
        },
        vllm_args={
            "tokenizer_mode": "mistral",
            "load_format": "mistral",
            "config_format": "mistral",
            "tensor_parallel_size": 2,
        },
    ),
)


def create_mistral22b_resource() -> BaseLlmResource:
    return create_llm_resource(mistral22b_config)
