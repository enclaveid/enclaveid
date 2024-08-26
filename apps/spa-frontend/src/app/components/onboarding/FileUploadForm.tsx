import { useState } from 'react';
import { Button } from '../atoms/Button';
import { GoogleIcon, OpenAiIcon } from '../atoms/Icons';
import { FileUploadSection } from './FileUploadSection';
import { FormCardLayout } from '../FormCardLayout';

export interface FileUploadFormProps {
  uploadUrl?: string;
  onNext?: () => void;
  onSkip?: () => void;
}

// TODO: instruction video link
export function FileUploadForm({
  uploadUrl,
  onNext,
  onSkip,
}: FileUploadFormProps) {
  const [success, setSuccess] = useState(false);

  return (
    <div className="h-screen flex items-center justify-center bg-[#F3F5F7]">
      <div className="flex flex-col gap-9 max-w-[597px] w-full mx-auto">
        <h1 className="text-[#6C7A8A] text-4xl font-medium leading-[-0.72px] text-center">
          Upload your data
        </h1>
        <FormCardLayout>
          <p className="description-text">
            To get started using EnclaveID you need to upload your personal
            data. Most data export tools take some time to generate the data
            archives, so feel free to close the window and come back later.
          </p>
          <div className="mt-9 flex flex-col gap-[18px]">
            <div className="flex items-center gap-[17px] flex-col rounded-md bg-white shadow pl-[15px] pt-[17pt] pr-[18px] pb-5">
              <div className="flex flex-col gap-[9px]">
                <div className="flex items-center gap-[17px]">
                  <button className="w-[55px] h-[55px]">
                    <GoogleIcon />
                  </button>
                  <span className="text-sm text-[#6C7A8A]">
                    Head over to{' '}
                    <a
                      href="https://takeout.google.com"
                      className="underline"
                      target="_blank"
                      rel="noreferrer"
                    >
                      takeout.google.com
                    </a>{' '}
                    to obtain a copy of your Google data and upload here the
                    archive. Make sure to select <b>My Activity</b> in{' '}
                    <b>JSON</b> format.{' '}
                    <a href="#" className="underline">
                      See instruction video
                    </a>
                  </span>
                  <FileUploadSection
                    uploadUrl={uploadUrl}
                    onSuccess={() => setSuccess(true)}
                  />
                </div>
              </div>
            </div>

            {/* <div className="flex items-center gap-[17px] flex-row rounded-md bg-white shadow pl-[15px] pt-[17pt] pr-[18px] pb-5">
              <FacebookIcon />
              <span className="text-[#6C7A8A] text-lg">Coming soon</span>
            </div> */}
            <div className="mb-9 flex items-center gap-[17px] flex-row rounded-md bg-white shadow pl-[15px] pt-[17pt] pr-[18px] pb-5">
              <OpenAiIcon />
              <span className="text-[#6C7A8A] text-lg">Coming soon</span>
            </div>
          </div>
          <p className="description-text">
            Your data will be processed in a confindential environment, making
            it inaccessible by anyone other than yourself.{' '}
            <a
              href="https://github.com/enclaveid/enclaveid"
              className="underline"
              target="_blank"
              rel="noreferrer"
            >
              Learn more
            </a>
          </p>
          <div className="mt-6 flex flex-col gap-[18px]">
            {success ? (
              <Button
                label="Next"
                fullWidth
                onClick={() => {
                  onNext && onNext();
                }}
              />
            ) : (
              <Button
                label="I'm waiting for the data export"
                fullWidth
                variant="secondary"
                onClick={() => {
                  onSkip && onSkip();
                }}
              />
            )}
          </div>
        </FormCardLayout>
      </div>
    </div>
  );
}
