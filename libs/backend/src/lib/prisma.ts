import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient({
  datasources: {
    db: {
      url:
        process.env.API_DATABASE_URL ||
        'postgres://enclaveid:enclaveid@enclaveid-postgresql.default.svc.cluster.local:5432/enclaveid_api',
    },
  },
  transactionOptions: {
    maxWait: 60 * 1000, // 1 minute
    timeout: 60 * 1000, // 1 minute
  },
});
