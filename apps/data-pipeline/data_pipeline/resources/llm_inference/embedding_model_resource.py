import gc
from typing import TYPE_CHECKING

import polars as pl
from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from pydantic import PrivateAttr

from data_pipeline.utils.capabilities import is_vllm_image

if is_vllm_image() or TYPE_CHECKING:
    import torch
    from torch import Tensor
    from torch.nn.parallel import DataParallel
    from transformers import AutoModel, AutoTokenizer
else:
    torch = None
    Tensor = None
    DataParallel = None
    AutoModel = None
    AutoTokenizer = None


class EmbeddingModelResource(ConfigurableResource):
    normalize_embeddings: bool = False

    _model_name = "Salesforce/SFR-Embedding-2_R"
    _max_length = 4096

    _model = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        logger = get_dagster_logger()

        logger.info(f"Loading SentenceTransformer model: {self._model_name}")
        self._device = torch.device("cuda")
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModel.from_pretrained(self._model_name)

        if torch.cuda.device_count() > 1:
            logger.info(f"Loading the model on {torch.cuda.device_count()} GPUs")
            self._model = DataParallel(self._model)

        self._model.to(self._device)

    def _last_token_pool(
        self, last_hidden_states: Tensor, attention_mask: Tensor
    ) -> Tensor:
        left_padding = attention_mask[:, -1].sum() == attention_mask.shape[0]
        if left_padding:
            return last_hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = last_hidden_states.shape[0]
            return last_hidden_states[
                torch.arange(batch_size, device=last_hidden_states.device),
                sequence_lengths,
            ]

    def get_embeddings(self, series: pl.Series):
        sentences = series.to_list()

        batch_dict = self._tokenizer(
            sentences,
            max_length=self._max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        batch_dict = {k: v.to(self._device) for k, v in batch_dict.items()}

        # Get embeddings
        with torch.no_grad():
            outputs = self._model(**batch_dict)

        # If using DataParallel, the output might be wrapped, so we need to access the tensor
        if isinstance(
            outputs.last_hidden_state,
            torch.nn.parallel.distributed.DistributedDataParallel,
        ):
            last_hidden_state = outputs.last_hidden_state.module
        else:
            last_hidden_state = outputs.last_hidden_state

        embeddings = self._last_token_pool(
            last_hidden_state, batch_dict["attention_mask"]
        )

        if self.normalize_embeddings:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=-1)

        return pl.Series(
            name="embeddings",
            values=embeddings.cpu().numpy(),
            dtype=pl.Array(pl.Float32, self._max_length),
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        del self._model

        torch.cuda.empty_cache()
        gc.collect()

        return super().teardown_after_execution(context)
