import { promisify } from 'util';
import yauzl from 'yauzl';

export async function readZip(
  zipBuffer: Buffer,
  fileName: string
): Promise<Buffer> {
  const fromBuffer = promisify<Buffer, yauzl.Options, yauzl.ZipFile>(
    yauzl.fromBuffer
  );
  const zipFile = await fromBuffer(zipBuffer, { lazyEntries: true });
  const openReadStream = promisify(zipFile.openReadStream.bind(zipFile));

  return new Promise<Buffer>((resolve, reject) => {
    let fileData: Buffer | null = null;

    zipFile.on('entry', async (entry) => {
      if (entry.fileName === fileName) {
        try {
          const readStream = await openReadStream(entry);
          const chunks: Buffer[] = [];

          readStream.on('data', (chunk) => chunks.push(chunk));
          readStream.on('end', () => {
            fileData = Buffer.concat(chunks);
            zipFile.close();
            resolve(fileData);
          });
        } catch (err) {
          reject(err);
        }
      } else {
        zipFile.readEntry();
      }
    });

    zipFile.on('error', reject);
    zipFile.on('end', () => {
      if (!fileData) {
        reject(new Error(`File ${fileName} not found in archive`));
      }
    });

    zipFile.readEntry();
  });
}
