from abc import ABC, abstractmethod
from typing import Callable, List, Tuple, Union

from dagster import Config, ConfigurableResource

from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig


class LlmConfig(Config):
    colloquial_model_name: str
    local_llm_config: LocalLlmConfig | None = None
    remote_llm_config: RemoteLlmConfig | None = None


PromptSequence = List[Union[str, Callable[[str], str]]]


class BaseLlmResource(ConfigurableResource, ABC):
    llm_config: LlmConfig

    @abstractmethod
    def setup_for_execution(self, context) -> None:
        pass

    @abstractmethod
    def get_prompt_sequences_completions_batch(
        self, prompt_sequences: List[PromptSequence]
    ) -> Tuple[List[List[str]], float]:
        pass

    @abstractmethod
    def teardown_after_execution(self, context) -> None:
        pass
