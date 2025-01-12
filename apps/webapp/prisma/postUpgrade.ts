import { PrismaClient } from '@prisma/client';
import { readFileSync } from 'fs';
import { join } from 'path';

const prisma = new PrismaClient();

async function runCustomMigrations() {
  try {
    // Read the SQL file containing vector index creation
    const sqlPath = join(__dirname, 'vector-indexes.sql');
    const sql = readFileSync(sqlPath, 'utf8');

    // Execute the SQL
    await prisma.$executeRawUnsafe(sql);

    console.log('Successfully created vector indexes');
  } catch (error) {
    console.error('Error creating vector indexes:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

runCustomMigrations().catch((e) => {
  console.error(e);
  process.exit(1);
});
