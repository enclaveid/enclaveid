from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


class Llama70bQuantizedResource(LocalLlmResource):
    _model_name = "neuralmagic/Meta-Llama-3.1-70B-Instruct-quantized.w8a16"
    _temperature = 0.6
    _top_p = 0.3
    _max_tokens = 1024
    _context_window = 1024 * 8
    _max_model_len = 1024 * 10 * 8
