import time
from typing import TYPE_CHECKING, Callable, Dict, List, Union

from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import is_vllm_image
from data_pipeline.utils.get_hf_cache_info import get_hf_cache_info

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

    _llm: LLM = PrivateAttr()
    _tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast] = PrivateAttr()
    _sampling_params: SamplingParams = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        logger = get_dagster_logger()

        logger.info(get_hf_cache_info())

        load_time_start = time.time()
        self._llm = LLM(self._model_name, enable_prefix_caching=True)
        load_time_end = time.time()

        logger.info(
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
        prompt_sequences_length = max(len(sequence) for sequence in prompt_sequences)
        conversations = [[] for _ in prompt_sequences]

        # Process each step in the prompt sequence up to the longest sequence
        for step in range(prompt_sequences_length):
            current_prompts = []
            indices_to_process = []

            for i, sequence in enumerate(prompt_sequences):
                if step < len(sequence):
                    prompt = sequence[step]
                    if callable(prompt):
                        conversations[i].append(
                            {
                                "role": "user",
                                "content": prompt(conversations[i][-1]["content"]),
                            }
                        )
                    else:
                        conversations[i].append({"role": "user", "content": prompt})

                    indices_to_process.append(i)
                    current_prompts.append(conversations[i])

            if not current_prompts:
                continue

            completions = self._get_completions_batch(current_prompts)

            for idx, completion in zip(indices_to_process, completions):
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
