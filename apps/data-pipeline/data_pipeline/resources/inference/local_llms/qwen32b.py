from data_pipeline.resources.inference.local_llms.local_llm_resource import (
    LocalLlmResource,
)


class Qwen32bResource(LocalLlmResource):
    _model_name = "Qwen/Qwen2.5-32B-Instruct"
    _sampling_params_args = {
        "max_tokens": 2048,
    }
    _vllm_args = {
        "tensor_parallel_size": 2,
    }
