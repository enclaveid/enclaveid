from typing import TYPE_CHECKING, Any, Dict, List

from dagster import ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    from data_pipeline.resources.inference.local_llms.local_llm import (
        LocalLlm,
        PromptSequence,
    )
else:
    LocalLlm = None
    PromptSequence = None


class LocalLlmResource(ConfigurableResource):
    _model_name: str = PrivateAttr()
    _sampling_params_args: Dict[str, Any] = PrivateAttr()
    _vllm_args: Dict[str, Any] = PrivateAttr()

    _local_llm: LocalLlm = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)

        self._local_llm = LocalLlm(
            self._model_name,
            self._logger,
            self._vllm_args,
            self._sampling_params_args,
        )

    def get_prompt_sequences_completions_batch(
        self,
        prompt_sequences: List[PromptSequence],
    ):
        return self._local_llm.get_prompt_sequences_completions_batch(prompt_sequences)

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        self._local_llm.cleanup()

        self._logger.info("Done freeing GPU memory...")
        self._logger.info(gpu_info())

        return super().teardown_after_execution(context)
