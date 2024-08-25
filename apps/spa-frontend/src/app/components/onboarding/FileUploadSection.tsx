// TODO: this library kinda sucks
import { Dropzone, ExtFile, FileMosaic } from '@files-ui/react';
import * as React from 'react';

interface FileUploadSectionProps {
  uploadUrl: string;
  onSuccess: () => void;
}

export function FileUploadSection(props: FileUploadSectionProps) {
  const { uploadUrl, onSuccess } = props;

  const [extFiles, setExtFiles] = React.useState([]);

  const onDelete = (id) => {
    setExtFiles(extFiles.filter((x) => x.id !== id));
  };
  const handleAbort = (id) => {
    setExtFiles(
      extFiles.map((ef) => {
        if (ef.id === id) {
          return { ...ef, uploadStatus: 'aborted' };
        } else return { ...ef };
      }),
    );
  };

  React.useEffect(() => {
    if (extFiles.length > 0) {
      const file = extFiles[0];
      if (file.xhr && file.xhr.status === 201) {
        onSuccess();
      }
    }
  }, [extFiles, onSuccess]);

  return (
    <Dropzone
      onChange={setExtFiles}
      minHeight="80px"
      value={extFiles}
      accept="application/zip"
      maxFiles={1}
      maxFileSize={200 * 1024 * 1024}
      label="Upload file"
      uploadConfig={{
        asBlob: true,
        autoUpload: true,
        cleanOnUpload: true,
        headers: {
          'Content-Type': 'application/zip',
          'x-ms-blob-type': 'BlockBlob',
        },
        method: 'PUT',
        url: uploadUrl,
      }}
      onError={(error) => console.error(error)}
    >
      {extFiles.map((file: ExtFile) => {
        return file.xhr ? (
          file.xhr.status === 201 ? (
            <FileMosaic
              {...file}
              uploadStatus="success"
              key={file.id}
              resultOnTooltip={false}
            />
          ) : (
            <FileMosaic
              {...file}
              key={file.id}
              onDelete={() => onDelete(file.id)}
              onAbort={() => handleAbort(file.id)}
              resultOnTooltip={false}
            />
          )
        ) : (
          <FileMosaic {...file} key={file.id} resultOnTooltip={false} />
        );
      })}
    </Dropzone>
  );
}
