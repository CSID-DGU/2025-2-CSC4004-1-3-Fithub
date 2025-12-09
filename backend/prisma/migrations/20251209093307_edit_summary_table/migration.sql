/*
  Warnings:

  - You are about to drop the column `filePath` on the `Summary` table. All the data in the column will be lost.
  - You are about to drop the column `keywords` on the `Summary` table. All the data in the column will be lost.
  - You are about to drop the column `quality` on the `Summary` table. All the data in the column will be lost.
  - You are about to drop the column `repo_id` on the `Summary` table. All the data in the column will be lost.
  - You are about to drop the column `summary` on the `Summary` table. All the data in the column will be lost.
  - You are about to drop the `CodeSummary` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `ContextMeta` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `Embedding` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `Graph` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `GraphEdge` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `GraphNode` table. If the table is not empty, all the data it contains will be lost.
  - Added the required column `content` to the `Summary` table without a default value. This is not possible if the table is not empty.
  - Added the required column `repoId` to the `Summary` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "CodeSummary" DROP CONSTRAINT "CodeSummary_projectId_fkey";

-- DropForeignKey
ALTER TABLE "CodeSummary" DROP CONSTRAINT "CodeSummary_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "ContextMeta" DROP CONSTRAINT "ContextMeta_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "Embedding" DROP CONSTRAINT "Embedding_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "Embedding" DROP CONSTRAINT "Embedding_summaryId_fkey";

-- DropForeignKey
ALTER TABLE "Graph" DROP CONSTRAINT "Graph_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "GraphEdge" DROP CONSTRAINT "GraphEdge_from_id_fkey";

-- DropForeignKey
ALTER TABLE "GraphEdge" DROP CONSTRAINT "GraphEdge_graphId_fkey";

-- DropForeignKey
ALTER TABLE "GraphEdge" DROP CONSTRAINT "GraphEdge_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "GraphEdge" DROP CONSTRAINT "GraphEdge_to_id_fkey";

-- DropForeignKey
ALTER TABLE "GraphNode" DROP CONSTRAINT "GraphNode_graphId_fkey";

-- DropForeignKey
ALTER TABLE "GraphNode" DROP CONSTRAINT "GraphNode_repo_id_fkey";

-- DropForeignKey
ALTER TABLE "Summary" DROP CONSTRAINT "Summary_repo_id_fkey";

-- AlterTable
ALTER TABLE "Summary" DROP COLUMN "filePath",
DROP COLUMN "keywords",
DROP COLUMN "quality",
DROP COLUMN "repo_id",
DROP COLUMN "summary",
ADD COLUMN     "content" JSONB NOT NULL,
ADD COLUMN     "repoId" BIGINT NOT NULL;

-- DropTable
DROP TABLE "CodeSummary";

-- DropTable
DROP TABLE "ContextMeta";

-- DropTable
DROP TABLE "Embedding";

-- DropTable
DROP TABLE "Graph";

-- DropTable
DROP TABLE "GraphEdge";

-- DropTable
DROP TABLE "GraphNode";

-- AddForeignKey
ALTER TABLE "Summary" ADD CONSTRAINT "Summary_repoId_fkey" FOREIGN KEY ("repoId") REFERENCES "repository"("repo_id") ON DELETE RESTRICT ON UPDATE CASCADE;
