from dagster import Config


class LocalLlmConfig(Config):
    model_name: str
    sampling_params_args: dict
    vllm_args: dict
