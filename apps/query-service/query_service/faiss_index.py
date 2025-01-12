import os
from typing import List

import faiss
import numpy as np
import polars as pl
from azure.storage.blob import BlobServiceClient

BASE_PATH = "dagster/speculatives_substantiation"


def download_azure_files(user_id: str) -> bytes:
    """Download specific user file from Azure Blob Storage into memory."""
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

    blob_path = f"{BASE_PATH}/{user_id}.snappy"
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    # Download directly to memory
    return blob_client.download_blob().readall()


class FaissIndex:
    def __init__(self, user_id: str):
        # Download and process data
        blob_data = download_azure_files(user_id)
        self.df = pl.read_parquet(blob_data)

        # Create FAISS index
        embeddings = np.stack(self.df["embedding"].to_numpy()).astype(np.float32)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

    def search(self, query_vector: np.ndarray, k: int = 30) -> List[dict]:
        similarities, indices = self.index.search(query_vector, k)

        # Get labels for the matched indices and combine with similarities
        labels = self.df["label"].to_numpy()[indices[0]]
        results = [
            {"label": label, "score": float(score)}
            for label, score in zip(labels, similarities[0])
        ]
        return results
