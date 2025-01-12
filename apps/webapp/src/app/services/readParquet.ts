import { parquetRead } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';

export async function readParquet(fileBuffer: Buffer): Promise<any> {
  const arrayBuffer = fileBuffer.buffer.slice(
    fileBuffer.byteOffset,
    fileBuffer.byteOffset + fileBuffer.byteLength
  );
  return new Promise((resolve) => {
    parquetRead({
      file: arrayBuffer,
      compressors,
      rowFormat: 'object',
      onComplete: (data) => {
        resolve(data);
      },
    });
  });
}
