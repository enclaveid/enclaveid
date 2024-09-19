from data_pipeline.resources.llm_inference.local.local_llm_resource import (
    LocalLlmResource,
)


class Llama70bQuantizedResource(LocalLlmResource):
    _model_name = "neuralmagic/Meta-Llama-3.1-70B-Instruct-quantized.w8a16"
    _sampling_params_args = {
        "temperature": 0.6,
        "top_p": 0.3,
        "max_tokens": 1024,
    }
    _vllm_args = {
        # We use 80k instead of the default 128k to avoid OOM errors
        "max_model_len": 1024 * 80,
        "tensor_parallel_size": 4,
    }
