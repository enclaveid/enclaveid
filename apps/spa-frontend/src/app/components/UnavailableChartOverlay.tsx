import { useNavigate } from 'react-router-dom';
import { Button } from './atoms/Button';
import toast from 'react-hot-toast';
import { getPressureMessage } from '../utils/feedbackMessages';

type UnavailableChartOverlayReason = 'no_data' | 'not_implemented';

const labels: Record<UnavailableChartOverlayReason, string> = {
  no_data:
    'Please complete the questionnaire to unlock this report. It will greatly help us improve the product for everyone <3',
  not_implemented:
    'The inference model for this report is not implemented.\n We will send you an email when it becomes available.',
};

export function UnavailableChartOverlay({
  enabled,
  reason,
  children,
}: {
  enabled?: boolean;
  reason: UnavailableChartOverlayReason;
  children: React.ReactNode;
}) {
  const navigate = useNavigate();

  return enabled ? (
    <div className="relative w-full">
      <div className="opacity-30 pointer-events-none">{children}</div>
      <div className="absolute inset-0 flex items-center justify-center p-10">
        <div className="bg-white p-4 rounded-lg shadow-lg flex flex-col gap-4">
          <p className="text-md text-passiveLinkColor text-center whitespace-pre-line">
            {labels[reason]}
          </p>
          {reason === 'no_data' ? (
            <Button
              label="Finish the questionnaire"
              variant="primary"
              onClick={() => {
                navigate('/onboarding/questionnaire', { replace: true });
              }}
            />
          ) : (
            <Button
              label="Pressure the developers"
              variant="secondary"
              onClick={() => {
                toast.success(getPressureMessage(), { duration: 8 * 1000 });
              }}
            />
          )}
        </div>
      </div>
    </div>
  ) : (
    children
  );
}
