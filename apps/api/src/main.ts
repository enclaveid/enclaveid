import Fastify from 'fastify';
import { initializePodsBuffer } from './app/services/fakeOauth/kubernetes';

// Plugins
import confidentiality from './app/plugins/confidentiality';
import cookie from './app/plugins/cookie';
import cors from './app/plugins/cors';
import helmet from './app/plugins/helmet';
import jwtAuth from './app/plugins/jwtAuth';
import prismaLifecycle from './app/plugins/prismaLifecycle';
import trpcAdapter from './app/plugins/trpcAdapter';
import fastifyHealthcheck from 'fastify-healthcheck';

const host = process.env.API_HOST ?? 'localhost';
const port = process.env.API_PORT ? Number(process.env.API_PORT) : 3000;

const server = Fastify({
  logger: true,
  maxParamLength: 5000,
});

server.register(confidentiality);
server.register(cookie);
server.register(cors);
server.register(helmet);
server.register(jwtAuth);
server.register(prismaLifecycle);
server.register(trpcAdapter);
server.register(fastifyHealthcheck);

// Start listening.
server.listen({ port, host }, (err) => {
  if (err) {
    server.log.error(err);
    process.exit(1);
  } else {
    console.log(`[ ready ] http://${host}:${port}`);

    if (process.env.ENABLE_FAKE_OAUTH === 'true')
      initializePodsBuffer()
        .then(() => {
          console.log('[ fakeOauth ] Pods buffer initialized');
        })
        .catch((err) => {
          console.error('[ fakeOauth ] Pods buffer initialization failed', err);
        });
  }
});
