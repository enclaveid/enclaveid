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
  // User with incomplete profile
  await prisma.user.create({
    data: {
      id: 'do_not_use',

      email: 'john.does.not@example.com',
      password: await hash('password'),

      confirmationCode: '',
      confirmedAt: new Date(),

      displayName: 'John Does Not',
      gender: Gender.FE,
      geographyLat: 0.0,
      geographyLon: 0.0,
    },
  });

  // User with complete profile
  await prisma.user.create({
    data: {
      id: 'clxenc3fw0007gzz3pdz6enfe',

      email: 'john.doe@example.com',
      password: await hash('password'),

      confirmationCode: '',
      confirmedAt: new Date(),

      displayName: 'John Doe',
      gender: Gender.MA,
      geographyLat: 0.0,
      geographyLon: 0.0,

      userTraits: {
        create: {
          sixteenPersonalityFactor: {
            create: {
              warmth: 0.4,
              reasoning: 0.6,
              emotionalStability: 0.3,
              dominance: 0.8,
              liveliness: 0.25,
              ruleConsciousness: 0.55,
              socialBoldness: 0.2,
              sensitivity: 0.75,
              vigilance: 0.35,
              abstractedness: 0.65,
              privateness: 0.45,
              apprehension: 0.7,
              opennessToChange: 0.25,
              selfReliance: 0.55,
              perfectionism: 0.35,
              tension: 0.8,
              summary:
                "This is a summary of the user's sixteen personality factors.",
            },
          },
          mbti: {
            create: {
              extraversion: true,
              sensing: false,
              thinking: true,
              judging: true,
              summary: "This is a summary of the user's MBTI type.",
            },
          },
          politicalCompass: {
            create: {
              economic: 0.5,
              social: 0.5,
              summary: "This is a summary of the user's political compass.",
            },
          },
          riasec: {
            create: {
              realistic: 0.5,
              investigative: 0.5,
              artistic: 0.5,
              social: 0.5,
              enterprising: 0.5,
              conventional: 0.5,
              summary: "This is a summary of the user's RIASEC type.",
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
