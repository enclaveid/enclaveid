import { StrictMode } from 'react';
import * as ReactDOM from 'react-dom/client';

import { App } from './app/app';
import { FileProvider } from './app/FileContext';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement,
);
root.render(
  <StrictMode>
    <FileProvider>
      <App />
    </FileProvider>
  </StrictMode>,
);
