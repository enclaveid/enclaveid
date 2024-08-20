import {
  generateBlobSASQueryParameters,
  BlobSASPermissions,
} from '@azure/storage-blob';
import { DataProvider } from '@enclaveid/shared';
import {
  azureContainerClient,
  azureDefaultContainerName,
  azureStorageCredentials,
} from './client';

export async function generateSasUrl(
  dataProvider: DataProvider,
  userId: string,
): Promise<string> {
  const blobName = `${userId}/${dataProvider.toLowerCase()}/latest.zip`;

  const sasOptions = {
    containerName: azureDefaultContainerName,
    blobName,
    permissions: BlobSASPermissions.parse('w'),
    startsOn: new Date(),
    expiresOn: new Date(3600 * 1000 * 24 + new Date().valueOf()), // URL valid for 1 day
  };

  const sasToken = generateBlobSASQueryParameters(
    sasOptions,
    azureStorageCredentials,
  ).toString();

  return `${azureContainerClient.url}/${blobName}?${sasToken}`;
}

export async function streamingUpload(filename, file) {
  const blockBlobClient = azureContainerClient.getBlockBlobClient(filename);
  return await blockBlobClient.uploadStream(file);
}
