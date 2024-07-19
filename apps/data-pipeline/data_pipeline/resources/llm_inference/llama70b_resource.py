from data_pipeline.resources.llm_inference.remote_llm_resource import RemoteLlmResource


class Llama70bResource(RemoteLlmResource):
    _concurrency_limit = 60
    _timeout = 60 * 10
    _inference_url = "https://Meta-Llama-3-70B-Instruct-pbssd-serverless.eastus2.inference.ai.azure.com/v1/chat/completions"
    _inference_config = {
        "max_tokens": 1024,
        "temperature": 0.8,
        "top_p": 0.1,
        "best_of": 1,
        "presence_penalty": 0,
        "use_beam_search": "false",
        "ignore_eos": "false",
        "skip_special_tokens": "false",
        "logprobs": "false",
    }
