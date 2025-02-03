/*
  Warnings:

  - You are about to drop the column `number` on the `PhoneNumber` table. All the data in the column will be lost.
  - A unique constraint covering the columns `[phoneNumber]` on the table `PhoneNumber` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `phoneNumber` to the `PhoneNumber` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "PhoneNumber_number_key";

-- AlterTable
ALTER TABLE "ApiKey" ALTER COLUMN "key" SET DEFAULT encode(sha256(random()::text::bytea), 'hex');

-- AlterTable
ALTER TABLE "PhoneNumber" DROP COLUMN "number",
ADD COLUMN     "phoneNumber" TEXT NOT NULL;

-- AlterTable
ALTER TABLE "User" ALTER COLUMN "email" DROP NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "PhoneNumber_phoneNumber_key" ON "PhoneNumber"("phoneNumber");
