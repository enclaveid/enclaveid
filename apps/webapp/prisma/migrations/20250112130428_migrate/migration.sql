/*
  Warnings:

  - A unique constraint covering the columns `[apiKey]` on the table `User` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "User" ADD COLUMN     "apiKey" CHAR(64) NOT NULL DEFAULT encode(sha256(random()::text::bytea), 'hex');

-- CreateIndex
CREATE UNIQUE INDEX "User_apiKey_key" ON "User"("apiKey");
