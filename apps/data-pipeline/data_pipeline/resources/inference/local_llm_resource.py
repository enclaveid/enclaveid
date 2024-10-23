import itertools
from typing import TYPE_CHECKING, List

import ray
from dagster import InitResourceContext
from pydantic import PrivateAttr

from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.resources.inference.local_llm_config import LocalLlmConfig
from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    import torch

    from data_pipeline.resources.inference.local_llm import LocalLlm
else:
    LocalLlm = None
    torch = None


class LocalLlmResource(BaseLlmResource):
    llm_config: LocalLlmConfig

    _local_llms: List[ray.ObjectRef] = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)
        ray.init(object_store_memory=200 * 1024 * 1024 * 1024)  # 200GB
        num_actors = (
            torch.cuda.device_count()
            // self.llm_config.vllm_args["tensor_parallel_size"]
        )

        self._local_llms = [
            LocalLlm.options(
                num_gpus=self.llm_config.vllm_args["tensor_parallel_size"]
            ).remote(
                self.llm_config.model_name,
                self.llm_config.vllm_args,
                self.llm_config.sampling_params_args,
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
