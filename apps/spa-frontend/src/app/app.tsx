import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { BreadcrumbProvider } from './providers/BreadcrumbContext';

import { AuthProvider } from './providers/AuthProvider';
import { StreamChatProvider } from './providers/StreamChatProvider';
import { reactRouter } from './reactRouter';

export function App() {
  return (
    <AuthProvider>
      <StreamChatProvider>
        <BreadcrumbProvider>
          <RouterProvider router={reactRouter} />
          <Toaster position="bottom-right" reverseOrder={false} />
        </BreadcrumbProvider>
      </StreamChatProvider>
    </AuthProvider>
  );
}
