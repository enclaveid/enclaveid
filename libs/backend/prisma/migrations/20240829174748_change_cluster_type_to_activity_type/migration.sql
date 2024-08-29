/*
  Warnings:

  - Changed the type of `clusterType` on the `InterestsCluster` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.

*/
-- AlterTable
ALTER TABLE "InterestsCluster" DROP COLUMN "clusterType",
ADD COLUMN     "clusterType" "ActivityType" NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "InterestsCluster_userInterestsId_pipelineClusterId_clusterT_key" ON "InterestsCluster"("userInterestsId", "pipelineClusterId", "clusterType");
