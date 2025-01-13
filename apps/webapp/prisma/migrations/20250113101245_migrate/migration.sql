-- AlterTable
ALTER TABLE "User" ALTER COLUMN "apiKey" SET DEFAULT encode(sha256(random()::text::bytea), 'hex');
