import gc
import logging
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Union

from dagster import ConfigurableResource, DagsterLogManager, InitResourceContext
from pydantic import BaseModel, PrivateAttr

from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    import torch
    from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
    from vllm import LLM, SamplingParams
    from vllm.distributed.parallel_state import (
        destroy_distributed_environment,
        destroy_model_parallel,
    )
else:
    torch = None
    LLM = SamplingParams = None
    AutoTokenizer = PreTrainedTokenizer = PreTrainedTokenizerFast = None
    destroy_model_parallel = destroy_distributed_environment = None
    VLLM = None

PromptSequence = List[str] | List[Callable[[str | BaseModel], str]]


class LocalLlmResource(ConfigurableResource):
    _model_name: str = PrivateAttr()
    _sampling_params_args: Dict[str, Any] = PrivateAttr()
    _vllm_args: Dict[str, Any] = PrivateAttr()

    _llm: LLM = PrivateAttr()
    _tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast] = PrivateAttr()
    _sampling_params: SamplingParams = PrivateAttr()
    _logger: DagsterLogManager | logging.Logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)

        load_time_start = time.time()
        self._llm = LLM(
            self._model_name,
            enable_prefix_caching=True,
            # Set a context limit other than default if provided (depends on available GPU memory)
            **self._vllm_args,
        )
        load_time_end = time.time()

        self._logger.info(
            f"Loaded {self._model_name} in {load_time_end - load_time_start:.2f}s"
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._sampling_params = SamplingParams(**self._sampling_params_args)

    def _get_completions_batch(
        self,
        conversations: List[List[Dict[str, str]]],
    ) -> List[str]:
        templated_conversations = self._tokenizer.apply_chat_template(
            conversations,
            tokenize=False,
            add_generation_prompt=True,
        )

        return list(
            map(
                lambda res: res.outputs[0].text,
                self._llm.generate(
                    templated_conversations,
                    self._sampling_params,
                ),
            )
        )

    def get_prompt_sequences_completions_batch(
        self,
        prompt_sequences: List[PromptSequence],
    ):
        # Assume that all prompt sequences have the same length
        prompt_sequences_length = len(prompt_sequences[0])

        # The conversations array contains the raw user and assistant messages for generation
        conversations: List[List[Dict[str, str]]] = [[] for _ in prompt_sequences]
        # The results array contains the parsed assistant responses
        results = [[] for _ in prompt_sequences]

        # Process each step in the prompt sequence up to the longest sequence
        for step in range(prompt_sequences_length):
            for i, sequence in enumerate(prompt_sequences):
                prompt = sequence[step]
                if callable(prompt):
                    if step == 0:
                        raise ValueError(
                            "First prompt in the sequence cannot be a function"
                        )
                    else:
                        conversations[i].append(
                            {
                                "role": "user",
                                "content": prompt(conversations[i][-1]["content"]),
                            }
                        )
                else:
                    conversations[i].append({"role": "user", "content": prompt})

            time_start = time.time()
            self._logger.info(f"Generating completions for step {step}...")
            completions = self._get_completions_batch(conversations)
            self._logger.info(
                f"Done generating completions for step {step} in {(time.time() - time_start):.2f}s"
            )

            for idx, completion in enumerate(completions):
                conversations[idx].append(
                    {
                        "role": "assistant",
                        "content": completion,
                    }
                )
                results[idx].append(completion)

        return results, conversations

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        self._logger.info("Freeing GPU memory...")
        destroy_model_parallel()
        destroy_distributed_environment()
        del self._llm.llm_engine.model_executor
        del self._llm
        gc.collect()
        torch.cuda.empty_cache()

        self._logger.info("Done freeing GPU memory...")
        self._logger.info(gpu_info())

        return super().teardown_after_execution(context)
