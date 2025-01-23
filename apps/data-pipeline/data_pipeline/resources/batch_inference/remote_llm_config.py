from dagster import Config


class RemoteLlmConfig(Config):
    api_key: str
    concurrency_limit: int
    timeout: int
    inference_url: str
    inference_config: dict
    input_cpm: float
    output_cpm: float
    context_length: int
