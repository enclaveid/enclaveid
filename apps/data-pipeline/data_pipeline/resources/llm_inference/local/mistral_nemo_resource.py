from data_pipeline.resources.llm_inference.local.local_llm_resource import (
    LocalLlmResource,
)


class MistralNemoResource(LocalLlmResource):
    _model_name = "mistralai/Mistral-Nemo-Instruct-2407"
    _sampling_params_args = {
        "temperature": 1,
        "top_p": 1,
        "max_tokens": 1024,
    }
    _vllm_args = {
        "tokenizer_mode": "mistral",
        "load_format": "mistral",
        "config_format": "mistral",
    }
