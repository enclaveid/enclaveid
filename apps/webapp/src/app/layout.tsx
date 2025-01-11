//import '../../../../libs/ui-utils/src/global.css';

import '@enclaveid/ui-utils/global.css';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'EnclaveID',
  description: 'Get LLMs to know you',
  icons: {
    icon: [
      {
        media: '(prefers-color-scheme: light)',
        url: '/logo-dark.svg',
        href: '/logo-dark.svg',
      },
      {
        media: '(prefers-color-scheme: dark)',
        url: '/logo-light.svg',
        href: '/logo-light.svg',
      },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
