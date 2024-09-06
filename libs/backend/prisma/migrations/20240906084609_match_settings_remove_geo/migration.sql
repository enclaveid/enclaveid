/*
  Warnings:

  - You are about to drop the column `geographyLat` on the `User` table. All the data in the column will be lost.
  - You are about to drop the column `geographyLon` on the `User` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "User" DROP COLUMN "geographyLat",
DROP COLUMN "geographyLon",
ADD COLUMN     "matchingEnabled" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "sensitiveMatchingEnabled" BOOLEAN NOT NULL DEFAULT false;
