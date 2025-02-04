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
      name: 'Giovanni',
      phoneNumbers: {
        create: {
          phoneNumber: process.env.TEST_PHONE_NUMBER_1!,
          verifiedAt: new Date(),
        },
      },
      apiKeys: {
        create: {
          key: '1234567890',
        },
      },
    },
  });

  await prisma.user.create({
    data: {
      email: 'changeme@gmail.com',
      name: 'Estela',
      phoneNumbers: {
        create: {
          phoneNumber: process.env.TEST_PHONE_NUMBER_2!,
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
