/*
  Warnings:

  - Made the column `userId` on table `ClaimCategory` required. This step will fail if there are existing NULL values in that column.

*/
-- DropForeignKey
ALTER TABLE "ApiKey" DROP CONSTRAINT "ApiKey_userId_fkey";

-- DropForeignKey
ALTER TABLE "ClaimCategory" DROP CONSTRAINT "ClaimCategory_userId_fkey";

-- DropForeignKey
ALTER TABLE "UserClaim" DROP CONSTRAINT "UserClaim_claimCategoryId_fkey";

-- AlterTable
ALTER TABLE "ApiKey" ALTER COLUMN "key" SET DEFAULT encode(sha256(random()::text::bytea), 'hex');

-- AlterTable
ALTER TABLE "ClaimCategory" ALTER COLUMN "userId" SET NOT NULL;

-- AddForeignKey
ALTER TABLE "ApiKey" ADD CONSTRAINT "ApiKey_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserClaim" ADD CONSTRAINT "UserClaim_claimCategoryId_fkey" FOREIGN KEY ("claimCategoryId") REFERENCES "ClaimCategory"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ClaimCategory" ADD CONSTRAINT "ClaimCategory_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
