import { ContainerClient } from '@azure/storage-blob';
import archiver from 'archiver';
import { PassThrough, Readable } from 'stream';
import { azureContainerClient } from './client';
import { generateSasUrl } from './streamingUpload';

export async function createExportZip(userId: string): Promise<string> {
  // Get a reference to the container
  const containerClient: ContainerClient = azureContainerClient.output;

  // Create a pass-through stream
  const passThrough = new PassThrough();

  // Create the archive
  const archive = archiver('zip', {
    zlib: { level: 9 }, // Sets the compression level
  });

  // Pipe archive data to the pass-through stream
  archive.pipe(passThrough);

  // Create a blob client for the new zip file
  const zipBlobClient = containerClient.getBlockBlobClient(
    `data_exports/${userId}.zip`,
  );

  // Start uploading from the stream
  const uploadPromise = zipBlobClient.uploadStream(passThrough);

  for await (const blob of containerClient.listBlobsFlat()) {
    if (
      blob.name.endsWith(`${userId}.snappy`) &&
      !blob.name.startsWith('data_exports/')
    ) {
      // Download the blob content
      const blobClient = containerClient.getBlobClient(blob.name);
      const downloadBlockBlobResponse = await blobClient.download();

      // Convert RetriableReadableStream to Readable
      const readableStream = Readable.from(
        await downloadBlockBlobResponse.readableStreamBody,
      );

      // Add the file to the archive
      archive.append(readableStream, { name: blob.name });
    }
  }

  // Finalize the archive
  await archive.finalize();

  // Wait for the upload to complete
  await uploadPromise;

  return generateSasUrl(userId);
}
