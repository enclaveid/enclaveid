import os

from azure.storage.blob import BlobServiceClient

BASE_PATH = "dagster/speculatives_substantiation"


def download_azure_files(user_id: str) -> bytes:
    """Download specific user file from Azure Blob Storage into memory."""
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

    if not account_name or not account_key or not container_name:
        raise ValueError("Azure storage environment variables are not set")

    blob_path = f"{BASE_PATH}/{user_id}.snappy"
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)

    # Download directly to memory
    return blob_client.download_blob().readall()
