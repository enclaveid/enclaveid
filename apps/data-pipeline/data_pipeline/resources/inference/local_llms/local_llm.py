import gc
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import ray
import torch
from dagster import get_dagster_logger
from pydantic import BaseModel, PrivateAttr
from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
from vllm import LLM, SamplingParams
from vllm.distributed.parallel_state import (
    destroy_distributed_environment,
    destroy_model_parallel,
)

PromptSequence = List[str] | List[Callable[[str | BaseModel], str]]


@ray.remote(num_gpus=1)
class LocalLlm:
    _llm: LLM = PrivateAttr()
    _tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast] = PrivateAttr()
    _sampling_params: SamplingParams = PrivateAttr()
    _logger = PrivateAttr()

    def __init__(
        self,
        model_name: str,
        vllm_args: Optional[Dict[str, Any]] = None,
        sampling_params_args: Optional[Dict[str, Any]] = None,
    ):
        self._logger = get_dagster_logger()
        vllm_args = vllm_args or {}
        sampling_params_args = sampling_params_args or {}

        load_time_start = time.time()
        self._llm = LLM(
            model_name,
            enable_prefix_caching=True,
            **vllm_args,
        )

        self._logger.info(
            f"Loaded {model_name} in {time.time() - load_time_start:.2f}s"
        )

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._sampling_params = SamplingParams(**sampling_params_args)

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
    ) -> Tuple[List[List[str]], List[List[Dict[str, str]]]]:
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

    def cleanup(self) -> None:
        self._logger.info("Freeing GPU memory...")
        destroy_model_parallel()
        destroy_distributed_environment()
        del self._llm.llm_engine.model_executor
        del self._llm
        gc.collect()
        torch.cuda.empty_cache()
