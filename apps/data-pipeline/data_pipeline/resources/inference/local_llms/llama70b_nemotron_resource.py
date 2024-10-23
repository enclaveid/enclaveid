from data_pipeline.resources.inference.local_llms.local_llm_resource import (
    LocalLlmResource,
)


class Llama70bNemotronResource(LocalLlmResource):
    _model_name = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
    _sampling_params_args = {
        "max_tokens": 2048,
    }
    _vllm_args = {
        # "max_model_len": 1024 * 80,
        "tensor_parallel_size": 4,
    }
