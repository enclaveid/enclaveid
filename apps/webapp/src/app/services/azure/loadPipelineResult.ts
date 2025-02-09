import { azureContainerClient } from './storage';
import path from 'path';
import fs from 'fs';

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
  if (process.env.NODE_ENV === 'development') {
    const localPath = path.join(
      process.cwd(),
      '..',
      'data-pipeline',
      'data',
      blobName
    );

    return new Promise((resolve, reject) => {
      fs.readFile(localPath, (err: any, data: Buffer) => {
        if (err) reject(err);
        else resolve(data);
      });
    });
  } else {
    // Get a reference to the blob
    const blobClient = azureContainerClient.getBlobClient(blobName);

    // Download the blob content
    const downloadResponse = await blobClient.download();
    if (!downloadResponse.readableStreamBody) {
      throw new Error('Failed to download blob');
    }

    return await streamToBuffer(downloadResponse.readableStreamBody);
  }
}
