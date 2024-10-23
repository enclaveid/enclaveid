from dagster import get_dagster_logger

from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.inference.local_llm_resource import LocalLlmResource
from data_pipeline.resources.inference.remote_llm_resource import RemoteLlmResource
from data_pipeline.utils.capabilities import is_vllm_image


def create_llm_resource(config: LlmConfig) -> BaseLlmResource | None:
    logger = get_dagster_logger()

    if is_vllm_image():
        if config.local_llm_config is None:
            logger.warning(
                f"Local LLM config not found for model: {config.colloquial_model_name}"
            )
        else:
            return LocalLlmResource(llm_config=config.local_llm_config)

    if config.remote_llm_config is None:
        logger.warning(
            f"Remote LLM config not found for model: {config.colloquial_model_name}"
        )
    else:
        return RemoteLlmResource(llm_config=config.remote_llm_config)
