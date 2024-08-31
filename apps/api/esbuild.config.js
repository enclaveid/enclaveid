const { sentryEsbuildPlugin } = require("@sentry/esbuild-plugin");

require("esbuild").build({
  bundle: true,
  sourcemap: true, // Source map generation must be turned on
  plugins: [
    // Put the Sentry esbuild plugin after all other plugins
    sentryEsbuildPlugin({
      authToken: process.env.SENTRY_AUTH_TOKEN,
      org: "enclaveid",
      project: "node-fastify",
    }),
  ],
  outExtension: { ".js": ".js" },
});
