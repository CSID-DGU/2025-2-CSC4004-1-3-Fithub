/*
  Warnings:

  - You are about to drop the `Summary` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `SummaryItem` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "Summary" DROP CONSTRAINT "Summary_repoId_fkey";

-- DropForeignKey
ALTER TABLE "SummaryItem" DROP CONSTRAINT "SummaryItem_summaryId_fkey";

-- DropTable
DROP TABLE "Summary";

-- DropTable
DROP TABLE "SummaryItem";

-- CreateTable
CREATE TABLE "Graph" (
    "id" SERIAL NOT NULL,
    "runId" TEXT NOT NULL,
    "repoId" BIGINT NOT NULL,
    "context" JSONB,
    "metrics" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Graph_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GraphNode" (
    "id" SERIAL NOT NULL,
    "graphId" INTEGER NOT NULL,
    "nodeId" TEXT NOT NULL,
    "label" TEXT,
    "type" TEXT,
    "parent" TEXT,
    "domain" TEXT,
    "importance" DOUBLE PRECISION,
    "summary" TEXT,
    "summaryDetails" JSONB,
    "context" JSONB,

    CONSTRAINT "GraphNode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GraphEdge" (
    "id" SERIAL NOT NULL,
    "graphId" INTEGER NOT NULL,
    "source" TEXT NOT NULL,
    "target" TEXT NOT NULL,
    "type" TEXT,

    CONSTRAINT "GraphEdge_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Recommendation" (
    "id" SERIAL NOT NULL,
    "runId" TEXT NOT NULL,
    "repoId" BIGINT NOT NULL,
    "target" TEXT,
    "reason" TEXT,
    "priority" TEXT,
    "category" TEXT,
    "type" TEXT,
    "confidence" INTEGER,
    "rank" INTEGER,
    "relatedNodes" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Recommendation_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Graph" ADD CONSTRAINT "Graph_repoId_fkey" FOREIGN KEY ("repoId") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphNode" ADD CONSTRAINT "GraphNode_graphId_fkey" FOREIGN KEY ("graphId") REFERENCES "Graph"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_graphId_fkey" FOREIGN KEY ("graphId") REFERENCES "Graph"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Recommendation" ADD CONSTRAINT "Recommendation_repoId_fkey" FOREIGN KEY ("repoId") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;
