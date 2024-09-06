import { useNavigate } from 'react-router-dom';
import { Button } from './atoms/Button';
import toast from 'react-hot-toast';
import { getPressureMessage } from '../utils/feedbackMessages';
import { useEffect, useMemo, useState } from 'react';
import { useOnboardingStatus } from '../providers/OnboardingStatusProvider';
import { OnboardingStatusKey } from '../types/trpc';

type UnavailableChartOverlayReason =
  | 'no_questionnaire'
  | 'not_implemented'
  | 'no_data'
  | 'processing';

const labels: Record<UnavailableChartOverlayReason, string> = {
  no_data: 'Please upload your data to see this report.',
  processing:
    'Your data is currently being processed. You will receive an email when it is ready.',
  no_questionnaire:
    'Please complete the questionnaire to unlock this report. It will greatly help us improve the product for everyone <3',
  not_implemented:
    'The inference model for this report is not implemented.\n We will send you an email when it becomes available.',
};

export function UnavailableChartOverlay({
  enabledOverride,
  questionnaireStatusKey,
  reasonOverride,
  children,
}: {
  enabledOverride?: boolean;
  questionnaireStatusKey?: OnboardingStatusKey;
  children: React.ReactNode;
  reasonOverride?: UnavailableChartOverlayReason;
}) {
  const navigate = useNavigate();

  const [reason, setReason] =
    useState<UnavailableChartOverlayReason>(reasonOverride);

  const { onboardingStatus } = useOnboardingStatus();
  const [enabled, setEnabled] = useState<boolean>(true);

  useEffect(() => {
    if (reasonOverride) {
      setReason(reasonOverride);
    } else {
      if (onboardingStatus) {
        if (
          questionnaireStatusKey &&
          !onboardingStatus[questionnaireStatusKey]
        ) {
          setReason('no_questionnaire');
        } else if (!onboardingStatus.isUserDataUploaded?.google) {
          setReason('no_data');
        } else if (!onboardingStatus.isDataProcessed) {
          setReason('processing');
          // This is optional only for those reports that require a questionnaire
        } else {
          if (enabledOverride !== undefined) {
            setEnabled(enabledOverride);
          } else {
            setEnabled(false);
          }
        }
      }
    }
  }, [
    onboardingStatus,
    reasonOverride,
    questionnaireStatusKey,
    enabledOverride,
  ]);

  const callToActionElement = useMemo(() => {
    switch (reason) {
      case 'no_questionnaire':
        return (
          <Button
            label="Finish the questionnaire"
            variant="primary"
            onClick={() => {
              navigate('/onboarding/questionnaire', { replace: true });
            }}
          />
        );
      case 'not_implemented':
        return (
          <Button
            label="Pressure the developers"
            variant="secondary"
            onClick={() => {
              toast.success(getPressureMessage(), { duration: 5 * 1000 });
            }}
          />
        );
      case 'no_data':
        return (
          <Button
            label="Upload your data"
            variant="primary"
            onClick={() => {
              navigate('/onboarding/fileUpload', { replace: true });
            }}
          />
        );
      default:
        return null;
    }
  }, [reason, navigate]);

  return enabled ? (
    <div className="relative w-full">
      <div className="opacity-20 pointer-events-none">{children}</div>
      <div className="absolute inset-0 flex items-center justify-center p-10">
        <div className="bg-white p-4 rounded-lg shadow-lg flex flex-col gap-4">
          <p className="text-md text-passiveLinkColor text-center whitespace-pre-line">
            {labels[reason]}
          </p>
          {callToActionElement}
        </div>
      </div>
    </div>
  ) : (
    children
  );
}
