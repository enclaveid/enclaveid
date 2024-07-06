from typing import TYPE_CHECKING, Dict, List, Union

from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.utils.is_cuda_available import is_cuda_available

if is_cuda_available() or TYPE_CHECKING:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
    from vllm import LLM, SamplingParams
else:
    torch = None
    SentenceTransformer = None
    LLM = SamplingParams = None
    AutoTokenizer = PreTrainedTokenizer = PreTrainedTokenizerFast = None


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
        logger.info(f"Loading {self._model_name}...")

        self._llm = LLM(self._model_name)
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

    def get_prompt_sequences_completions_batch(self, prompt_sequences: List[List[str]]):
        all_completions = []
        max_length = max(len(sequence) for sequence in prompt_sequences)
        current_conversations = [[] for _ in prompt_sequences]

        # Process each step in the prompt sequence up to the longest sequence
        for step in range(max_length):
            current_prompts = []
            indices_to_process = []

            for i, sequence in enumerate(prompt_sequences):
                if step < len(sequence):
                    current_conversations[i].append(
                        {"role": "user", "content": sequence[step]}
                    )
                    indices_to_process.append(i)
                    current_prompts.append(current_conversations[i])

            if not current_prompts:
                continue

            completions = self._get_completions_batch(current_prompts)

            for idx, completion in zip(indices_to_process, completions):
                current_conversations[idx].append(
                    {"role": "assistant", "content": completion}
                )

        # Extract the final completions for each sequence
        for conversation in current_conversations:
            if conversation:
                all_completions.append(conversation[-1]["content"])

        return all_completions
