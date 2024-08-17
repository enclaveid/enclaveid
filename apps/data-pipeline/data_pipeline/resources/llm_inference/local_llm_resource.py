import gc
import logging
import time
from typing import TYPE_CHECKING, Callable, Dict, List, Union

from dagster import ConfigurableResource, DagsterLogManager, InitResourceContext
from pydantic import BaseModel, PrivateAttr

from data_pipeline.utils.capabilities import gpu_info, is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    import torch
    from outlines.models.vllm import VLLM
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
    _temperature: float = PrivateAttr()
    _top_p: float = PrivateAttr()
    _max_tokens: int = PrivateAttr()
    _context_window: int = PrivateAttr()
    _max_model_len: int | None = PrivateAttr()

    _llm: LLM = PrivateAttr()
    _tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast] = PrivateAttr()
    _sampling_params: SamplingParams = PrivateAttr()
    _logger: DagsterLogManager | logging.Logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)

        # logger.info(get_hf_cache_info())

        load_time_start = time.time()
        self._llm = LLM(
            self._model_name,
            enable_prefix_caching=True,
            tensor_parallel_size=2,
            # Set a context limit other than default if provided (depends on available GPU memory)
            **(
                {"max_model_len": self._max_model_len}
                if self._max_model_len is not None
                else {}
            ),
        )
        load_time_end = time.time()

        self._logger.info(
            f"Loaded {self._model_name} in {load_time_end - load_time_start:.2f}s"
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._sampling_params = SamplingParams(
            temperature=self._temperature,
            top_p=self._top_p,
            max_tokens=self._max_tokens,
        )

    def _get_completions_batch(
        self,
        conversations: List[List[Dict[str, str]]],
        pydantic_model: BaseModel | None,
    ) -> List[str | BaseModel]:
        # Get the idxs of the inputs over self._context_window
        over_context = list(
            map(
                lambda x: x[0] if len(x[1]) > self._context_window else None,  # type: ignore
                enumerate(
                    self._tokenizer.apply_chat_template(
                        conversations,
                        add_generation_prompt=True,
                    )
                ),
            )
        )

        # Print indeces of the inputs that are over the context window
        if any(over_context):
            self._logger.warning(
                f"Conversation IDs over max context ({self._context_window}) length: {list(filter(lambda x: x is not None, over_context))}"
            )

        templated_conversations = self._tokenizer.apply_chat_template(
            conversations,
            tokenize=False,
            add_generation_prompt=True,
        )

        # If pydantic_model is provided, constrain the output
        # if pydantic_model:
        #     return json_generator(VLLM(self._llm), pydantic_model)(
        #         templated_conversations  # type: ignore
        #     )
        # else:
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
        pydantic_models: List,
    ):
        # Assume that all prompt sequences have the same length
        prompt_sequences_length = len(prompt_sequences[0])
        pydantic_models_length = len(pydantic_models)

        if pydantic_models_length != prompt_sequences_length:
            raise ValueError(
                f"Prompt sequences and pydantic models have different lengths: {prompt_sequences_length} and {pydantic_models_length}"
            )

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

            completions = self._get_completions_batch(
                conversations, pydantic_models[step]
            )

            for idx, completion in enumerate(completions):
                conversations[idx].append(
                    {
                        "role": "assistant",
                        "content": completion.model_dump_json()
                        if isinstance(completion, BaseModel)
                        else completion,
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
