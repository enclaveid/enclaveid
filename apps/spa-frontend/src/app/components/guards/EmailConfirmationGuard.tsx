import { Navigate, Outlet } from 'react-router-dom';
import { trpc } from '../../utils/trpc';
import { LoadingPage } from '../../pages/LoadingPage';

export function EmailConfirmationGuard({
  children,
}: {
  children?: React.ReactNode;
}) {
  const getEmailConfirmationStatusQuery =
    trpc.private.getEmailConfirmationStatus.useQuery();

  if (getEmailConfirmationStatusQuery.isLoading) {
    return <LoadingPage />;
  }

  if (
    getEmailConfirmationStatusQuery.isSuccess &&
    getEmailConfirmationStatusQuery.data
  ) {
    return children ?? <Outlet />;
  }

  return <Navigate to="/confirm-email" replace />;
}
