-- CreateTable
CREATE TABLE "Summary" (
    "id" SERIAL NOT NULL,
    "repo_id" BIGINT NOT NULL,
    "filePath" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "keywords" TEXT[],
    "quality" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Summary_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Embedding" (
    "id" SERIAL NOT NULL,
    "summaryId" INTEGER NOT NULL,
    "fusedVector" JSONB NOT NULL,
    "rawEdges" JSONB NOT NULL,
    "repo_id" BIGINT NOT NULL,

    CONSTRAINT "Embedding_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ContextMeta" (
    "id" SERIAL NOT NULL,
    "repo_id" BIGINT NOT NULL,
    "metaJson" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ContextMeta_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Graph" (
    "id" SERIAL NOT NULL,
    "repo_id" BIGINT NOT NULL,
    "graphJson" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Graph_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Embedding_summaryId_key" ON "Embedding"("summaryId");

-- CreateIndex
CREATE UNIQUE INDEX "ContextMeta_repo_id_key" ON "ContextMeta"("repo_id");

-- CreateIndex
CREATE UNIQUE INDEX "Graph_repo_id_key" ON "Graph"("repo_id");

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Task" ADD CONSTRAINT "Task_assigneeUserId_fkey" FOREIGN KEY ("assigneeUserId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Summary" ADD CONSTRAINT "Summary_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Embedding" ADD CONSTRAINT "Embedding_summaryId_fkey" FOREIGN KEY ("summaryId") REFERENCES "Summary"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Embedding" ADD CONSTRAINT "Embedding_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ContextMeta" ADD CONSTRAINT "ContextMeta_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Graph" ADD CONSTRAINT "Graph_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;
