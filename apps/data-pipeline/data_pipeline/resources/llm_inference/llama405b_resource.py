from data_pipeline.resources.llm_inference.remote_llm_resource import RemoteLlmResource


class Llama405bResource(RemoteLlmResource):
    _concurrency_limit = 60
    _timeout = 360 * 10
    _inference_url = "https://Meta-Llama-3-1-405B-Instruct-snx.eastus2.models.ai.azure.com/v1/chat/completions"
    _inference_config = {
        "max_tokens": 2048,
        "temperature": 1,
        "top_p": 0.5,
        "best_of": 1,
        "presence_penalty": 0,
        "use_beam_search": "false",
        "ignore_eos": "false",
        "skip_special_tokens": "false",
        "stream": False,
    }
