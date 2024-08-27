import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { BreadcrumbProvider } from './providers/BreadcrumbContext';

import { AuthProvider } from './providers/AuthProvider';
import { reactRouter } from './reactRouter';

export function App() {
  return (
    <AuthProvider>
      <BreadcrumbProvider>
        <RouterProvider router={reactRouter} />
        <Toaster position="bottom-right" reverseOrder={false} />
      </BreadcrumbProvider>
    </AuthProvider>
  );
}
