import torch
from ray import serve
from sentence_transformers import SentenceTransformer


@serve.deployment(ray_actor_options={"num_gpus": 1})
class EmbeddingService:
    def __init__(self, model_name="nvidia/NV-Embed-v2"):
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
        self.model.max_seq_length = 32768
        self.model.tokenizer.padding_side = "right"

    async def __call__(self, request):
        data = await request.json()

        inputs = data.get("inputs", [])

        if not inputs:
            return {"embeddings": []}

        normalize_embeddings = data.get("normalize_embeddings", True)
        batch_size = data.get("batch_size", 1)

        inputs_w_eos = [i + self.model.tokenizer.eos_token for i in inputs]

        try:
            embeddings = self.model.encode(
                inputs_w_eos,
                normalize_embeddings=normalize_embeddings,
                batch_size=batch_size,
            )
        except Exception as e:
            torch.cuda.empty_cache()
            return {"error": str(e)}

        return {"embeddings": embeddings.tolist()}


app = EmbeddingService.bind()
