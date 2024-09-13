import { FastifyInstance } from 'fastify';
import fp from 'fastify-plugin';
import { downloadPipelineResults } from '../services/azure/readDataframe';
import { processClusterMatches } from '../services/dataPipeline/processClusterMatches';
import { prisma } from '@enclaveid/backend';
import * as pl from 'nodejs-polars';
import { sendEmail } from '../services/azure/mailer';

export default fp(async (fastify: FastifyInstance) => {
  fastify.post('/webhooks/pipeline-finished', async (request, reply) => {
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

    if (!user) {
      reply.status(404).send({ error: 'User not found' });
      return;
    }

    const blobName = `results_for_api/${user.id}.snappy`;

    let df: pl.DataFrame;
    try {
      df = pl.readParquet(await downloadPipelineResults(blobName));
    } catch (err) {
      console.error(err);
      reply
        .status(500)
        .send({ error: 'Error reading Parquet file: ' + err.message });
      return;
    }

    try {
      await processClusterMatches(df);
    } catch (err) {
      console.error(err);
      reply
        .status(500)
        .send({ error: 'Error processing cluster matches: ' + err.message });
      return;
    }

    let emailError;
    try {
      if (process.env.SEND_RESULTS_EMAIL === 'true')
        await sendEmail(
          user.email,
          'Your EnclaveID results are ready!',
          `<html>
        <body>
          <p>Hi ${user.displayName},</p>
          <p>Your EnclaveID results are ready: https://app.enclaveid.com/dashboard</p>
          <p>The EnclaveID Team</p>
        </body>
      </html>`,
        );
    } catch (err) {
      emailError = err;
      console.error(err);
    }

    reply.send(
      emailError ? { success: true, error: emailError } : { success: true },
    );
  });
});
