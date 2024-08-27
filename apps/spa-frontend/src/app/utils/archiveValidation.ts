import JSZip from 'jszip';

export async function validateGoogleTakoutZip(zipFile: File): Promise<boolean> {
  return await JSZip.loadAsync(zipFile).then((zip) => {
    const myActivityFile = zip.file(
      'Takeout/My Activity/Search/MyActivity.json',
    );

    return !!myActivityFile;
  });
}
