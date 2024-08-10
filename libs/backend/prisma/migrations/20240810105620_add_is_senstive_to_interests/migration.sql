-- DropForeignKey
ALTER TABLE "InterestsClusterMatch" DROP CONSTRAINT "InterestsClusterMatch_interestsClustersSimilarityId_fkey";

-- DropForeignKey
ALTER TABLE "UserMatch" DROP CONSTRAINT "UserMatch_usersOverallSimilarityId_fkey";

-- AlterTable
ALTER TABLE "InterestsCluster" ADD COLUMN     "isSensitive" BOOLEAN NOT NULL DEFAULT false;

-- AddForeignKey
ALTER TABLE "InterestsClusterMatch" ADD CONSTRAINT "InterestsClusterMatch_interestsClustersSimilarityId_fkey" FOREIGN KEY ("interestsClustersSimilarityId") REFERENCES "InterestsClustersSimilarity"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserMatch" ADD CONSTRAINT "UserMatch_usersOverallSimilarityId_fkey" FOREIGN KEY ("usersOverallSimilarityId") REFERENCES "UsersOverallSimilarity"("id") ON DELETE CASCADE ON UPDATE CASCADE;
