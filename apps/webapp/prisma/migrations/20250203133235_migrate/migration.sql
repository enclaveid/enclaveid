/*
  Warnings:

  - You are about to drop the `MessagingPartner` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "MessagingPartner" DROP CONSTRAINT "MessagingPartner_userId_fkey";

-- AlterTable
ALTER TABLE "ApiKey" ALTER COLUMN "key" SET DEFAULT encode(sha256(random()::text::bytea), 'hex');

-- DropTable
DROP TABLE "MessagingPartner";

-- CreateTable
CREATE TABLE "PhoneNumber" (
    "id" TEXT NOT NULL,
    "number" TEXT NOT NULL,
    "verificationCode" TEXT,
    "verifiedAt" TIMESTAMP(3),
    "userId" TEXT NOT NULL,

    CONSTRAINT "PhoneNumber_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "PhoneNumber_number_key" ON "PhoneNumber"("number");

-- AddForeignKey
ALTER TABLE "PhoneNumber" ADD CONSTRAINT "PhoneNumber_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
