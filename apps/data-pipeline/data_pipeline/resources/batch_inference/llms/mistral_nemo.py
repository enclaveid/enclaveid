from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.local_llm_config import LocalLlmConfig

mistral_nemo_config = LlmConfig(
    colloquial_model_name="mistral_nemo",
    local_llm_config=LocalLlmConfig(
        model_name="mistralai/Mistral-Nemo-Instruct-2407",
        sampling_params_args={
            "max_tokens": 1024,
        },
        vllm_args={
            "tokenizer_mode": "mistral",
            "load_format": "mistral",
            "config_format": "mistral",
            "tensor_parallel_size": 1,
        },
    ),
)


def create_mistral_nemo_resource() -> BaseLlmResource:
    return create_llm_resource(mistral_nemo_config)
