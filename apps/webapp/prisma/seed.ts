import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
});

async function main() {
  await prisma.user.create({
    data: {
      id: 'cm0i27jdj0000aqpa73ghpcxf',
      email: 'magogagiovanni@gmail.com',
      apiKeys: {
        create: {
          key: '1234567890',
        },
      },
    },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
