import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
  transactionOptions: {
    maxWait: 60 * 1000, // 1 minute
    timeout: 60 * 1000, // 1 minute
  },
});

// TODO: This is from the Auth.js docs, not sure if it's needed
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
