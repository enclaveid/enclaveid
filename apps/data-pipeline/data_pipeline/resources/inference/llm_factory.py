from dagster import get_dagster_logger
from pydantic import BaseModel

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig
from data_pipeline.resources.inference.local_llm_resource import LocalLlmResource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig
from data_pipeline.resources.inference.remote_llm_resource import RemoteLlmResource
from data_pipeline.utils.capabilities import is_vllm_image


class LlmConfig(BaseModel):
    colloquial_model_name: str
    local_llm_config: LocalLlmConfig | None = None
    remote_llm_config: RemoteLlmConfig | None = None


def create_llm_resource(config: LlmConfig) -> BaseLlmResource:
    if is_vllm_image():
        if config.local_llm_config is None:
            get_dagster_logger().warning(
                f"Local LLM config not found for model: {config.colloquial_model_name}"
            )
        else:
            return LocalLlmResource(config=config.local_llm_config)

    if config.remote_llm_config is None:
        raise ValueError(
            f"Remote LLM config not found for model: {config.colloquial_model_name}"
        )
    else:
        return RemoteLlmResource(config=config.remote_llm_config)
