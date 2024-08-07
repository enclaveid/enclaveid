from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


class Llama8bResource(LocalLlmResource):
    _model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    _temperature = 0.8
    _top_p = 0.95
    _max_tokens = 1024
