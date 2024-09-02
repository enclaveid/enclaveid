/*
  Warnings:

  - The `activityDates` column on the `InterestsCluster` table would be dropped and recreated. This will lead to data loss if there is data in the column.

*/
-- AlterTable
ALTER TABLE "InterestsCluster" DROP COLUMN "activityDates",
ADD COLUMN     "activityDates" TIMESTAMP(3)[];
