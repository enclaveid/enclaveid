from pydantic import BaseModel


class LocalLlmConfig(BaseModel):
    model_name: str
    sampling_params_args: dict
    vllm_args: dict
