from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


class Gemma27bResource(LocalLlmResource):
    _model_name = "google/gemma-2-27b-it"
    _temperature = 0.8
    _top_p = 0.1
    _max_tokens = 1024