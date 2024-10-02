from data_pipeline.resources.inference.local_llms.local_llm_resource import (
    LocalLlmResource,
)


class Llama70bBf16Resource(LocalLlmResource):
    _model_name = "meta-llama/Llama-3.1-70B-Instruct"
    _sampling_params_args = {
        "max_tokens": 2048,
    }
    _vllm_args = {
        # "max_model_len": 1024 * 80,
        "tensor_parallel_size": 4,
    }
