import { DataProvider } from '@enclaveid/shared';
import { getBlobName } from '../azure/streamingUpload';
import { azureContainerClient } from '../azure/client';

export async function getIsUserDataUploaded(userId: string) {
  const blobName = getBlobName(DataProvider.GOOGLE, userId);

  const blobClient = azureContainerClient.getBlobClient(blobName);

  // Check if blob exists
  const blobExists = await blobClient.exists();

  return {
    google: blobExists,
  };
}
