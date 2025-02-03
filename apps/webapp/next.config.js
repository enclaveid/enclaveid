//@ts-check


const { composePlugins, withNx } = require('@nx/next');

/**
 * @type {import('@nx/next/plugins/with-nx').WithNxOptions}
 **/
const nextConfig = {
  nx: {
    // Set this to true if you would like to use SVGR
    // See: https://github.com/gregberge/svgr
    svgr: false,
  },
};

const plugins = [
  // Add more Next.js plugins to this list if needed.
  withNx,
];

module.exports = {
  ...composePlugins(...plugins)(nextConfig),
  webpack(config, { isServer }) {
    config.plugins.push(
      require('unplugin-icons/webpack').default({
        compiler: 'jsx',
        jsx: 'react',
        autoInstall: true,
      })
    )

    if (isServer) {
      config.externals.push({ 'nodejs-polars': 'commonjs nodejs-polars' });
    }

    return config;
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};
