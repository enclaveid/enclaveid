import itertools
from typing import TYPE_CHECKING, Any, Dict, List

import ray
from dagster import ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    import torch

    from data_pipeline.resources.inference.local_llms.local_llm import (
        LocalLlm,
        PromptSequence,
    )
else:
    LocalLlm = None
    PromptSequence = None
    torch = None


class LocalLlmResource(ConfigurableResource):
    _model_name: str = PrivateAttr()
    _sampling_params_args: Dict[str, Any] = PrivateAttr()
    _vllm_args: Dict[str, Any] = PrivateAttr()

    _local_llms: List[ray.ObjectRef] = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)
        ray.init()
        num_actors = (
            torch.cuda.device_count() // self._vllm_args["tensor_parallel_size"]
        )

        self._local_llms = [
            LocalLlm.options(num_gpus=self._vllm_args["tensor_parallel_size"]).remote(
                self._model_name,
                self._vllm_args,
                self._sampling_params_args,
            )
            for _ in range(num_actors)
        ]

    def get_prompt_sequences_completions_batch(
        self,
        prompt_sequences: List[PromptSequence],
    ):
        num_actors = len(self._local_llms)
        chunk_size = len(prompt_sequences) // num_actors
        remainder = len(prompt_sequences) % num_actors

        # Split the prompt_sequences into chunks, maintaining order
        chunks = []
        start = 0
        for i in range(num_actors):
            end = start + chunk_size + (1 if i < remainder else 0)
            chunks.append(prompt_sequences[start:end])
            start = end

        futures = [
            local_llm.get_prompt_sequences_completions_batch.remote(chunk)
            for local_llm, chunk in zip(self._local_llms, chunks)
        ]

        completions, metadata = zip(*ray.get(futures))
        return (list(itertools.chain(*completions)), list(itertools.chain(*metadata)))

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        refs = [local_llm.cleanup.remote() for local_llm in self._local_llms]
        ray.get(refs)

        self._logger.info("Done freeing GPU memory...")
        self._logger.info(gpu_info())
        ray.shutdown()

        return super().teardown_after_execution(context)
