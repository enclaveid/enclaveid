"""FastAPI service implementing FAISS similarity search with request queue."""
from typing import List, Optional

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from query_service.db import get_user_id_from_api_key
from query_service.embedding_client import EmbeddingClient
from query_service.faiss_index import FaissIndex

DEFAULT_K = 30


# Define request/response models
class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = DEFAULT_K


class SearchResponse(BaseModel):
    results: List[dict]


# Move embedding client to dependency
def get_embedding_client():
    """Dependency to get embedding client."""
    return EmbeddingClient()


app = FastAPI()


@app.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    authorization: str = Header(..., description="API key for authentication"),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
):
    """Handle search requests."""
    # Authenticate API key
    user_id = get_user_id_from_api_key(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Process directly since FastAPI handles concurrent requests
        query_vector = np.array(
            embedding_client.get_embeddings([request.query])[0],
            dtype=np.float32,
        ).reshape(1, -1)

        faiss_index = FaissIndex(user_id)
        results = faiss_index.search(query_vector, request.k or DEFAULT_K)

        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Search operation failed: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
