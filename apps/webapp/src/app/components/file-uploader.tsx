import { parquetRead } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';
import React from 'react';
import { useFileData } from './file-content';

export function FileUploader() {
  const { setFileData } = useFileData();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const form = e.target as HTMLFormElement;
      const file1 = (form.file1 as HTMLInputElement).files?.[0];

      if (file1) {
        const arrayBuffer1 = await file1.arrayBuffer();
        await parquetRead({
          file: arrayBuffer1,
          compressors,
          rowFormat: 'object',
          onComplete: (data) => {
            console.log('File data:', data);
            setFileData(data);
          },
        });
      }
    } catch (error) {
      console.error('Error loading parquet file:', error);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-50 p-8">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md bg-white rounded-lg shadow-md p-6"
      >
        <div className="mb-6">
          <label className="block">
            <span className="text-gray-700 font-medium">File:</span>
            <input
              type="file"
              name="file1"
              accept=".parquet,.snappy"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </label>
        </div>
        <button
          type="submit"
          className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition duration-150 ease-in-out"
        >
          Load File
        </button>
      </form>
      <div className="mt-4 text-gray-600">
        Check browser console for data after submitting
      </div>
    </div>
  );
}
