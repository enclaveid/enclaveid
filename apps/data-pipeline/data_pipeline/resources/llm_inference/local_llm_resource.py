import logging
import time
from typing import TYPE_CHECKING, Callable, Dict, List, Union

from dagster import ConfigurableResource, DagsterLogManager, InitResourceContext
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import is_vllm_image
from data_pipeline.utils.get_logger import get_logger

if is_vllm_image() or TYPE_CHECKING:
    import torch
    from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
    from vllm import LLM, SamplingParams
else:
    torch = None
    LLM = SamplingParams = None
    AutoTokenizer = PreTrainedTokenizer = PreTrainedTokenizerFast = None

PromptSequence = List[str] | List[Callable[[str], str]]


class LocalLlmResource(ConfigurableResource):
    _model_name: str = PrivateAttr()
    _temperature: float = PrivateAttr()
    _top_p: float = PrivateAttr()
    _max_tokens: int = PrivateAttr()
    _context_window: int = PrivateAttr()

    _llm: LLM = PrivateAttr()
    _tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast] = PrivateAttr()
    _sampling_params: SamplingParams = PrivateAttr()
    _logger: DagsterLogManager | logging.Logger = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._logger = get_logger(context)

        # logger.info(get_hf_cache_info())

        load_time_start = time.time()
        self._llm = LLM(self._model_name, enable_prefix_caching=True)
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
    ) -> List[str]:
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

        # TODO: How do we print the progress bar?
        results = self._llm.generate(
            self._tokenizer.apply_chat_template(
                conversations,
                tokenize=False,
                add_generation_prompt=True,
            ),
            self._sampling_params,
        )

        return list(map(lambda res: res.outputs[0].text, results))

    def get_prompt_sequences_completions_batch(
        self, prompt_sequences: List[PromptSequence]
    ):
        # Assume that all prompt sequences have the same length
        prompt_sequences_length = len(prompt_sequences[0])
        conversations = [[] for _ in prompt_sequences]

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

            completions = self._get_completions_batch(conversations)

            for idx, completion in enumerate(completions):
                conversations[idx].append({"role": "assistant", "content": completion})

        # Return all the assistant responses, only for completed conversations
        return list(
            map(
                lambda x: [message["content"] for message in x[1::2]]
                if len(x) == prompt_sequences_length * 2
                else [],
                conversations,
            )
        )
