import { LoadingPage } from '../../pages/LoadingPage';
import { useOnboardingSkips } from '../../providers/OnboardingSkipsProvider';
import { trpc } from '../../utils/trpc';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

interface OnboardingGuardProps {
  children?: React.ReactNode;
}

export function OnboardingGuard(props: OnboardingGuardProps) {
  const location = useLocation();
  const onboardingStatusQuery = trpc.private.getOnboardingStatus.useQuery();
  const { skips, reset: resetSkips } = useOnboardingSkips();

  if (location.pathname === '/onboarding') {
    return props.children ?? <Outlet />;
  }

  if (onboardingStatusQuery.isLoading) {
    return <LoadingPage />;
  }

  if (onboardingStatusQuery.isError) {
    console.error(
      'Error fetching onboarding status:',
      onboardingStatusQuery.error,
    );
    return <div>Error loading onboarding status. Please try again.</div>;
  }

  const {
    isPurposesComplete,
    isBigFiveComplete,
    isMoralFoundationsComplete,
    isUserDataUploaded,
  } = onboardingStatusQuery.data || {};

  const currentPath = location.pathname;

  // Define the order of onboarding steps, skipping steps if the user has skipped them
  const onboardingSteps = [
    { path: '/onboarding/purposeSelection', isComplete: isPurposesComplete },
    {
      path: '/onboarding/fileUpload',
      isComplete:
        isUserDataUploaded?.google || skips['/onboarding/fileUpload'].skipped,
    },
    {
      path: '/onboarding/questionnaire',
      isComplete:
        isBigFiveComplete &&
        isMoralFoundationsComplete &&
        !skips['/onboarding/questionnaire'].skipped,
    },
  ];

  // Find the first incomplete step
  const nextIncompleteStep = onboardingSteps.find((step) => !step.isComplete);

  // If we're not on the path of the next incomplete step, redirect
  if (nextIncompleteStep && currentPath !== nextIncompleteStep.path) {
    console.log(`Redirecting to ${nextIncompleteStep.path}`);
    return (
      <Navigate
        to={nextIncompleteStep.path}
        state={{
          from: location,
        }}
        replace
      />
    );
  }

  // If all steps are complete and we're still on an onboarding page, redirect to dashboard
  if (
    !nextIncompleteStep &&
    onboardingSteps.some((step) => currentPath.startsWith(step.path))
  ) {
    console.log('All onboarding complete, redirecting to dashboard');

    // Reset the skip flags
    resetSkips();

    return <Navigate to="/dashboard" state={{ from: location }} replace />;
  }

  // If we're here, either we're on the correct onboarding step or all steps are complete
  return props.children ?? <Outlet />;
}
