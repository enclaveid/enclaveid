from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


class Gemma9bResource(LocalLlmResource):
    _model_name = "google/gemma-2-9b-it"
    _temperature = 1.0
    _top_p = 1.0
    _max_tokens = 1024
    _max_model_len = None
    _enforce_eager = True
