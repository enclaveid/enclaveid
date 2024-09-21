from data_pipeline.resources.inference.local_llms.local_llm_resource import (
    LocalLlmResource,
)


class MistralNemoResource(LocalLlmResource):
    _model_name = "mistralai/Mistral-Nemo-Instruct-2407"
    _sampling_params_args = {
        "max_tokens": 1024,
    }
    _vllm_args = {
        "tokenizer_mode": "mistral",
        "load_format": "mistral",
        "config_format": "mistral",
        "tensor_parallel_size": 1,
    }
