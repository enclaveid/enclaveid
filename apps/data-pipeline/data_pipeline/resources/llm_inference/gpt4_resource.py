from data_pipeline.resources.llm_inference.remote_llm_resource import RemoteLlmResource


# TODO: Implement batch https://platform.openai.com/docs/api-reference/batch
class Gpt4Resource(RemoteLlmResource):
    _concurrency_limit = 256
    _timeout = 60 * 10
    _inference_url = "https://api.openai.com/v1/chat/completions"
    _inference_config = {
        "model": "gpt-4",
        "temperature": 1,
        "max_tokens": 1024,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
