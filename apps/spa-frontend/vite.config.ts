/// <reference types='vitest' />
import { sentryVitePlugin } from '@sentry/vite-plugin';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin';
import Icons from 'unplugin-icons/vite';

const buildInfoPlugin = () => {
  return {
    name: 'build-info',
    buildStart() {
      console.log('Build started at:', new Date().toISOString());
      console.log('Node version:', process.version);
      console.log('Project version:', process.env.npm_package_version);
      console.log('Build time variables:');
      console.log(
        Object.entries(process.env).forEach(([key, value]) => {
          if (key.startsWith('VITE_')) {
            console.log(`  ${key}: ${value}`);
          }
        }),
      );
    },
    closeBundle() {
      console.log('Build finished at:', new Date().toISOString());
    },
  };
};

export default defineConfig({
  root: __dirname,
  cacheDir: '../../node_modules/.vite/apps/spa-frontend',

  server: {
    port: 4200,
    host: 'localhost',
  },

  preview: {
    port: 4300,
    host: 'localhost',
  },

  plugins: [
    react(),
    nxViteTsPaths(),
    Icons({
      compiler: 'jsx',
      jsx: 'react',
      autoInstall: true, // experimental
    }),
    buildInfoPlugin(),
    sentryVitePlugin({
      org: 'enclaveid',
      project: 'javascript-react',
    }),
  ],

  build: {
    outDir: '../../dist/apps/spa-frontend',
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    sourcemap: true,
  },
  resolve: {
    alias: {
      '.prisma/client/index-browser':
        './node_modules/.prisma/client/index-browser.js',
    },
  },
  test: {
    globals: true,
    cache: {
      dir: '../../node_modules/.vitest',
    },
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],

    reporters: ['default'],
    coverage: {
      reportsDirectory: '../../coverage/apps/spa-frontend',
      provider: 'v8',
    },
  },
});
