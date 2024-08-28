import { azureContainerClient } from './client';

// Helper function to convert a ReadableStream to a Buffer
async function streamToBuffer(
  readableStream: NodeJS.ReadableStream,
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks = [];
    readableStream.on('data', (data) => {
      chunks.push(data instanceof Buffer ? data : Buffer.from(data));
    });
    readableStream.on('end', () => {
      resolve(Buffer.concat(chunks));
    });
    readableStream.on('error', reject);
  });
}

export async function downloadPipelineResults(
  blobName: string,
): Promise<Buffer> {
  // Get a reference to the blob
  const blobClient = azureContainerClient.getBlobClient(blobName);

  // Download the blob content
  const downloadResponse = await blobClient.download();
  const downloaded = await streamToBuffer(downloadResponse.readableStreamBody);

  return downloaded;
}
