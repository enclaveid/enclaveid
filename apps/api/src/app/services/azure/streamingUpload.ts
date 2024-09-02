import {
  generateBlobSASQueryParameters,
  BlobSASPermissions,
} from '@azure/storage-blob';
import { DataProvider } from '@enclaveid/shared';
import {
  azureContainerClient,
  azureInputContainerName,
  azureStorageCredentials,
} from './client';

export function getBlobName(dataProvider: DataProvider, userId: string) {
  return `${userId}/${dataProvider.toLowerCase()}/latest.zip`;
}

export async function generateSasUrl(
  dataProvider: DataProvider,
  userId: string,
): Promise<string> {
  const blobName = getBlobName(dataProvider, userId);

  const sasOptions = {
    containerName: azureInputContainerName,
    blobName,
    permissions: BlobSASPermissions.parse('w'),
    startsOn: new Date(),
    expiresOn: new Date(3600 * 1000 * 24 + new Date().valueOf()), // URL valid for 1 day
  };

  const sasToken = generateBlobSASQueryParameters(
    sasOptions,
    azureStorageCredentials,
  ).toString();

  return `${azureContainerClient.input.url}/${blobName}?${sasToken}`;
}

export async function streamingUpload(filename, file) {
  const blockBlobClient =
    azureContainerClient.input.getBlockBlobClient(filename);
  return await blockBlobClient.uploadStream(file);
}
