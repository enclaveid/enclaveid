import { Gender, PrismaClient } from '@prisma/client';
import { hash } from 'argon2';

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.API_DATABASE_URL,
    },
  },
});

async function main() {
  await prisma.user.create({
    data: {
      id: 'do_not_use',

      email: 'jane.doe@example.com',
      password: await hash('password'),

      confirmedAt: new Date(),

      displayName: 'Jane Doe',
      gender: Gender.Female,
      country: 'US',
      // geographyLat: 50.0,
      // geographyLon: 0.0,

      userTraits: {
        create: {
          bigFive: {
            create: {
              extraversion: 0.5,
              agreeableness: 0.5,
              conscientiousness: 0.5,
              neuroticism: 0.5,
              openness: 0.5,
            },
          },
          moralFoundations: {
            create: {
              authoritySubversion: 0.5,
              careHarm: 0.5,
              fairnessCheating: 0.5,
              loyaltyBetrayal: 0.5,
              sanctityDegradation: 0.5,
              goodCheck: 0.5,
              mathCheck: 0.5,
            },
          },
          mbti: {
            create: {
              extraversion: true,
              sensing: false,
              thinking: true,
              judging: true,
            },
          },
          politicalCompass: {
            create: {
              economic: 0.5,
              social: 0.5,
            },
          },
        },
      },
    },
  });

  await prisma.user.create({
    data: {
      id: 'clxenc3fw0007gzz3pdz6enfe',

      email: 'john.doe@example.com',
      password: await hash('password'),

      confirmedAt: new Date(),

      displayName: 'John Doe',
      gender: Gender.Male,
      country: 'US',
      // geographyLat: 0.0,
      // geographyLon: 50.0,

      userTraits: {
        create: {
          bigFive: {
            create: {
              extraversion: 1,
              agreeableness: 0.3,
              conscientiousness: 0.8,
              neuroticism: 0.4,
              openness: 0.5,
            },
          },
          moralFoundations: {
            create: {
              authoritySubversion: 0.3,
              careHarm: 0.8,
              fairnessCheating: 0.2,
              loyaltyBetrayal: 0.1,
              sanctityDegradation: 0.56,
              goodCheck: 0.5,
              mathCheck: 0.5,
            },
          },
          mbti: {
            create: {
              extraversion: true,
              sensing: false,
              thinking: true,
              judging: true,
            },
          },
          politicalCompass: {
            create: {
              economic: 0.5,
              social: 0.5,
            },
          },
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
