import { azureContainerClient } from './storage';

// Helper function to convert a ReadableStream to a Buffer
async function streamToBuffer(
  readableStream: NodeJS.ReadableStream
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    readableStream.on('data', (data) => {
      chunks.push(data instanceof Buffer ? data : Buffer.from(data));
    });
    readableStream.on('end', () => {
      resolve(Buffer.concat(chunks));
    });
    readableStream.on('error', reject);
  });
}

export async function loadPipelineResults(blobName: string): Promise<Buffer> {
  // Get a reference to the blob
  const blobClient = azureContainerClient.getBlobClient(blobName);

  // Download the blob content
  const downloadResponse = await blobClient.download();
  if (!downloadResponse.readableStreamBody) {
    throw new Error('Failed to download blob');
  }
  const downloaded = await streamToBuffer(downloadResponse.readableStreamBody);

  return downloaded;
}
