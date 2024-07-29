import { ReactElement, cloneElement } from 'react';
import { trpc } from '../../utils/trpc';
import { SidebarProps } from '../Sidebar';
import { useNavigate } from 'react-router-dom';

export function SidebarContainer({
  children,
}: {
  children: ReactElement<SidebarProps>;
}) {
  const logoutMutation = trpc.private.logout.useMutation();

  const navigate = useNavigate();

  return cloneElement(children, {
    onLogout: () => {
      localStorage.removeItem('userId');

      return logoutMutation.mutate(null, {
        onSuccess: () => {
          navigate('/login');
        },
      });
    },
  });
}
