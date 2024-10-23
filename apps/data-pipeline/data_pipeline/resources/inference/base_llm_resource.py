from abc import ABC, abstractmethod
from typing import Callable, List, Tuple, Union

from dagster import ConfigurableResource

from data_pipeline.resources.inference.llm_factory import LlmConfig

PromptSequence = List[Union[str, Callable[[str], str]]]


class BaseLlmResource(ConfigurableResource, ABC):
    config: LlmConfig

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
