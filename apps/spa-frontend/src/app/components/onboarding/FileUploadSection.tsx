import { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import toast from 'react-hot-toast';
import { validateGoogleTakoutZip } from '../../utils/archiveValidation';
import { PercentageCircle } from '../atoms/PercentageCircle';

export function FileUploadSection({ uploadUrl, onSuccess }) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const file = acceptedFiles[0];
      setError(null);
      setUploadProgress(0);

      const isValid = await validateGoogleTakoutZip(file);

      if (!isValid) {
        setError('This ZIP file does not contain MyActivity.json');
        return;
      }

      try {
        await axios.put(uploadUrl, file, {
          headers: {
            'Content-Type': 'application/zip',
            'x-ms-blob-type': 'BlockBlob',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);

            if (percentCompleted === 100) {
              onSuccess();
            }
          },
        });
      } catch (error) {
        setError(
          'Upload failed: ' + (error.response?.data?.message || error.message),
        );
      }
    },
    [uploadUrl, onSuccess],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    multiple: false,
  });

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  useEffect(() => {
    if (uploadProgress === 100) {
      toast.success('Uploaded!');
    }
  }, [uploadProgress]);

  return (
    <div className="p-4 border rounded-lg">
      <div
        {...getRootProps()}
        className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <input {...getInputProps()} />
        {uploadProgress > 0 ? (
          <div className="flex flex-col items-center">
            <PercentageCircle percentage={uploadProgress / 100.0} size="lg" />
          </div>
        ) : (
          <p className="text-gray-400">Upload here</p>
        )}
      </div>
    </div>
  );
}
