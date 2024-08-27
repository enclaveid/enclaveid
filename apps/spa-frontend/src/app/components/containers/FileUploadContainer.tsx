import { ReactElement, cloneElement } from 'react';
import { FileUploadFormProps } from '../onboarding/FileUploadForm';
import { trpc } from '../../utils/trpc';
import { DataProvider } from '@enclaveid/shared';
import { useLocation, useNavigate } from 'react-router-dom';
import { useOnboardingSkips } from '../../providers/OnboardingSkipsProvider';

export function FileUploadContainer({
  children,
}: {
  children: ReactElement<FileUploadFormProps>;
}) {
  const uploadUrlQuery = trpc.private.getUploadUrl.useQuery({
    dataProvider: DataProvider.GOOGLE,
  });

  const { skips } = useOnboardingSkips();

  const navigate = useNavigate();
  const location = useLocation();

  const trpcUtils = trpc.useUtils();

  return cloneElement(children, {
    uploadUrl: uploadUrlQuery.data?.url,
    onNext: () => {
      trpcUtils.private.getOnboardingStatus.invalidate().then(() => {
        navigate('/onboarding/questionnaire', { state: { from: location } });
      });
    },
    onSkip: () => {
      skips['/onboarding/fileUpload'].onSkip();
      navigate('/onboarding/questionnaire', { state: { from: location } });
    },
  });
}
