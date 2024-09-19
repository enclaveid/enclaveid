from data_pipeline.resources.llm_inference.local.local_llm_resource import (
    LocalLlmResource,
)


class Mistral22bResource(LocalLlmResource):
    _model_name = "mistralai/Mistral-Small-Instruct-2409"
    _sampling_params_args = {
        "max_tokens": 2048,
    }
    _vllm_args = {
        "tokenizer_mode": "mistral",
        "load_format": "mistral",
        "config_format": "mistral",
        "tensor_parallel_size": 2,
    }
