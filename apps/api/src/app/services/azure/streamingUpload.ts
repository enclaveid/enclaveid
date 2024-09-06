import {
  generateBlobSASQueryParameters,
  BlobSASPermissions,
} from '@azure/storage-blob';
import { DataProvider } from '@enclaveid/shared';
import {
  azureContainerClient,
  azureInputContainerName,
  azureOutputContainerName,
  azureStorageCredentials,
} from './client';

export function getBlobName(dataProvider: DataProvider, userId: string) {
  return `${userId}/${dataProvider.toLowerCase()}/latest.zip`;
}

/**
 * Generates a SAS URL for a blob in the Azure Blob Storage.
 * Since the SAS URL is only for the first and the very last user interaction iwht their data,
 * if dataProivder is specified, we use the input container, otherwise we use the output container.
 *
 * @param {string} userId - The user ID.
 * @param {DataProvider} [dataProvider] - The data provider.
 * @returns {Promise<string>} - The SAS URL.
 */
export async function generateSasUrl(
  userId: string,
  dataProvider?: DataProvider,
): Promise<string> {
  const containerName = dataProvider
    ? azureInputContainerName
    : azureOutputContainerName;

  const blobName = dataProvider
    ? getBlobName(dataProvider, userId)
    : `data_exports/${userId}.zip`;

  const sasOptions = {
    containerName,
    blobName,
    permissions: BlobSASPermissions.parse(dataProvider ? 'w' : 'r'),
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
