/* eslint-disable @typescript-eslint/no-non-null-assertion */
import {
  BlobServiceClient,
  StorageSharedKeyCredential,
} from '@azure/storage-blob';

const accountName = process.env.AZURE_STORAGE_ACCOUNT_NAME!;
const accountKey = process.env.AZURE_STORAGE_ACCOUNT_KEY!;
export const azureStorageCredentials = new StorageSharedKeyCredential(
  accountName,
  accountKey
);
const azureBlobServiceClient = new BlobServiceClient(
  `https://${accountName}.blob.core.windows.net`,
  azureStorageCredentials
);

export const azureInputContainerName = 'enclaveid-production-bucket';

export const azureContainerClient = azureBlobServiceClient.getContainerClient(
  azureInputContainerName
);
