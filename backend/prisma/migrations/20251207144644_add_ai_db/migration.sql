/*
  Warnings:

  - You are about to drop the column `level` on the `CodeSummary` table. All the data in the column will be lost.
  - You are about to drop the column `targetId` on the `CodeSummary` table. All the data in the column will be lost.
  - You are about to drop the column `graphJson` on the `Graph` table. All the data in the column will be lost.
  - You are about to drop the column `metadata` on the `GraphNode` table. All the data in the column will be lost.
  - You are about to drop the column `parent_id` on the `GraphNode` table. All the data in the column will be lost.
  - Added the required column `graphId` to the `GraphEdge` table without a default value. This is not possible if the table is not empty.
  - Added the required column `graphId` to the `GraphNode` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "commit" DROP CONSTRAINT "commit_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "file" DROP CONSTRAINT "file_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "issue" DROP CONSTRAINT "issue_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "pull" DROP CONSTRAINT "pull_repo_id_fkey";

-- AlterTable
ALTER TABLE "CodeSummary" DROP COLUMN "level",
DROP COLUMN "targetId";

-- AlterTable
ALTER TABLE "Graph" DROP COLUMN "graphJson";

-- AlterTable
ALTER TABLE "GraphEdge" ADD COLUMN     "graphId" INTEGER NOT NULL;

-- AlterTable
ALTER TABLE "GraphNode" DROP COLUMN "metadata",
DROP COLUMN "parent_id",
ADD COLUMN     "color" TEXT,
ADD COLUMN     "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN     "domain" TEXT,
ADD COLUMN     "graphId" INTEGER NOT NULL,
ADD COLUMN     "group" TEXT,
ADD COLUMN     "importance" DOUBLE PRECISION,
ADD COLUMN     "intent" TEXT,
ADD COLUMN     "logic" TEXT,
ADD COLUMN     "parent" TEXT,
ADD COLUMN     "size" DOUBLE PRECISION,
ADD COLUMN     "structure" TEXT,
ADD COLUMN     "summary" TEXT;

-- AlterTable
ALTER TABLE "Task" ADD COLUMN     "category" TEXT,
ADD COLUMN     "confidence" INTEGER,
ADD COLUMN     "priority" TEXT,
ADD COLUMN     "target" TEXT,
ADD COLUMN     "taskType" TEXT;

-- AddForeignKey
ALTER TABLE "commit" ADD CONSTRAINT "commit_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "file" ADD CONSTRAINT "file_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "issue" ADD CONSTRAINT "issue_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "pull" ADD CONSTRAINT "pull_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphNode" ADD CONSTRAINT "GraphNode_graphId_fkey" FOREIGN KEY ("graphId") REFERENCES "Graph"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphNode" ADD CONSTRAINT "GraphNode_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_graphId_fkey" FOREIGN KEY ("graphId") REFERENCES "Graph"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;
