import { FastifyInstance } from 'fastify';
import fp from 'fastify-plugin';
import { readPolarsFromAzure } from '../services/azure/readDataframe';
import { processClusterMatches } from '../services/dataPipeline/processClusterMatches';
import { prisma } from '@enclaveid/backend';
import { readParquet } from 'nodejs-polars';

export default fp(async (fastify: FastifyInstance) => {
  fastify.post('/pipeline_finished', async (request, reply) => {
    const { userId } = request.body as { userId: string };

    // Check if the user exists in the database
    const user = await prisma.user
      .findUnique({
        where: {
          id: userId,
        },
      })
      .catch((err) => {
        reply.status(404).send({ error: 'User not found' });
      });

    const blobName = `results_for_api/${userId}.snappy`;

    const df =
      process.env.NODE_ENV === 'development'
        ? readParquet(`${process.cwd()}/apps/data-pipeline/data/${blobName}`)
        : await readPolarsFromAzure(blobName);

    await processClusterMatches(df);

    reply.send({ success: true });
  });
});
