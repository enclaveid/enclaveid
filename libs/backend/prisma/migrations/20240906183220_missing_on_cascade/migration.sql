-- DropForeignKey
ALTER TABLE "InterestsClusterMatch" DROP CONSTRAINT "InterestsClusterMatch_interestsClusterId_fkey";

-- DropForeignKey
ALTER TABLE "UserMatch" DROP CONSTRAINT "UserMatch_userId_fkey";

-- AddForeignKey
ALTER TABLE "InterestsClusterMatch" ADD CONSTRAINT "InterestsClusterMatch_interestsClusterId_fkey" FOREIGN KEY ("interestsClusterId") REFERENCES "InterestsCluster"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserMatch" ADD CONSTRAINT "UserMatch_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
