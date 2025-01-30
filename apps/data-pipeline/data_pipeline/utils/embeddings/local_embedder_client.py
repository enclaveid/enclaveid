from typing import TYPE_CHECKING, List

from data_pipeline.constants.environments import get_environment
from data_pipeline.utils.embeddings.base_embedder_client import BaseEmbedderClient

if get_environment() == "LOCAL" or TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = object


class LocalEmbedderClient(BaseEmbedderClient):
    """
    Embedder that uses a local model on the CPU for development purposes.
    """

    _model: SentenceTransformer

    def __init__(self, model_name="nvidia/NV-Embed-v2"):
        self._model = SentenceTransformer(model_name, trust_remote_code=True)
        self._model.max_seq_length = 32768
        self._model.tokenizer.padding_side = "right"

    async def get_embeddings(
        self, texts: List[str], gpu_batch_size: int = 1, api_batch_size: int = 1
    ):
        if not texts:
            return []

        padded_texts = [i + self._model.tokenizer.eos_token for i in texts]

        embeddings = self._model.encode(
            padded_texts,
            normalize_embeddings=True,
            batch_size=gpu_batch_size,
        )

        return 0, embeddings.tolist()

    async def close(self) -> None:
        pass


if __name__ == "__main__":
    import asyncio

    async def main():
        client = LocalEmbedderClient()
        cost, embeddings = await client.get_embeddings(
            ["Hello, how are you? I'm under the water"]
        )
        print(cost)
        print(len(embeddings))

    asyncio.run(main())
