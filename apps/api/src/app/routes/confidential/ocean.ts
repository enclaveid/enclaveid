import { FastifyInstance } from 'fastify';
import { ZodTypeProvider } from 'fastify-type-provider-zod';
import { bigFiveSchema } from '../../types/schema/generated';

const schema = {
  response: {
    200: bigFiveSchema,
  },
};

export default async function (fastify: FastifyInstance) {
  fastify.withTypeProvider<ZodTypeProvider>().get(
    '/ocean',
    {
      onRequest: [fastify.authenticate],
      onResponse: [fastify.encryptResponse],
      schema,
    },
    async (request, reply) => {
      const user = await fastify.prisma.user.findUnique({
        where: { id: request.user.id },
        include: { userTraits: { include: { bigFive: true } } },
      });

      const bigFive = user?.userTraits?.bigFive;

      reply.send(bigFive);
    }
  );
}