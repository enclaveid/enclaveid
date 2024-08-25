import { forwardRef, ReactNode } from 'react';
import { DropzoneState } from 'react-dropzone';

interface DropzoneProps {
  children?: ReactNode;
  dropzone: DropzoneState;
}

const Dropzone = forwardRef<HTMLInputElement, DropzoneProps>(function Dropzone(
  { children, dropzone },
  ref
) {
  const { getRootProps, getInputProps, isDragActive } = dropzone;

  return (
    <div
      {...getRootProps()}
      className={`rounded-md bg-white shadow pl-[15px] pt-[17pt] pr-[18px] pb-5 dropzone ${
        isDragActive ? 'active' : ''
      }`}
    >
      <input {...getInputProps()} ref={ref} />
      {children}
    </div>
  );
});

export { Dropzone };
