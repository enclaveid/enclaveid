import os
from typing import List

import numpy as np
import requests


class EmbeddingClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self._api_key = api_key or os.getenv("EMBEDDING_API_KEY", "")
        self._base_url = base_url or os.getenv("EMBEDDING_BASE_URL", "")

    def _extract_and_normalize_embeddings(self, data: List[dict]) -> List[List[float]]:
        embeddings = np.array([d["embedding"] for d in data])
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts. Assumes immediate response."""
        print(f"Getting embeddings for {len(texts)} texts")

        # Add </s> token to each text
        texts = [text + " </s>" for text in texts]

        try:
            payload = {
                "input": {
                    "model": "nvidia/NV-Embed-v2",
                    "input": texts,
                }
            }

            response = requests.post(
                self._base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                    "api-key": self._api_key,
                },
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("output", {}).get("data"):
                print(f"Empty result received: {result}")
                return []

            return self._extract_and_normalize_embeddings(result["output"]["data"])

        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return []
