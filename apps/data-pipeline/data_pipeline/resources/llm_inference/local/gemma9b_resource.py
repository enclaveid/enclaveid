from data_pipeline.resources.llm_inference.local.local_llm_resource import LocalLlmResource


class Gemma9bResource(LocalLlmResource):
    _model_name = "google/gemma-2-9b-it"
    _sampling_params_args = {
        "temperature": 1.0,
        "top_p": 1.0,
        "max_tokens": 1024,
    }
    _vllm_args = {
        "enforce_eager": True,
    }
