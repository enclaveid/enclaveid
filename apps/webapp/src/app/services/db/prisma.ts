import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
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

globalForPrisma.prisma = prisma;
