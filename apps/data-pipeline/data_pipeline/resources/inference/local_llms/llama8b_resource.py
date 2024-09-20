from data_pipeline.resources.inference.local_llms.local_llm_resource import (
    LocalLlmResource,
)


class Llama8bResource(LocalLlmResource):
    _model_name = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    _sampling_params_args = {
        "temperature": 0.8,
        "top_p": 0.95,
        "max_tokens": 1024,
    }
    _vllm_args = {}
