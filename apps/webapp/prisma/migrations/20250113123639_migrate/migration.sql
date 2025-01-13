/*
  Warnings:

  - You are about to drop the column `apiKey` on the `User` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "User_apiKey_key";

-- AlterTable
ALTER TABLE "User" DROP COLUMN "apiKey";

-- CreateTable
CREATE TABLE "ApiKey" (
    "id" TEXT NOT NULL,
    "key" CHAR(64) NOT NULL DEFAULT encode(sha256(random()::text::bytea), 'hex'),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,

    CONSTRAINT "ApiKey_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ApiKey_key_key" ON "ApiKey"("key");

-- AddForeignKey
ALTER TABLE "ApiKey" ADD CONSTRAINT "ApiKey_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
