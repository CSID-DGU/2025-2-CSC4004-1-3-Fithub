-- CreateEnum
CREATE TYPE "Role" AS ENUM ('FRONTEND', 'BACKEND', 'AI', 'DEVOPS', 'DATABASE', 'COMMON');

-- CreateEnum
CREATE TYPE "TaskStatus" AS ENUM ('UNDONE', 'IN_PROGRESS', 'DONE');

-- CreateTable
CREATE TABLE "User" (
    "id" SERIAL NOT NULL,
    "githubId" TEXT NOT NULL,
    "login" TEXT NOT NULL,
    "avatarUrl" TEXT,
    "name" TEXT,
    "email" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "githubAccessToken" TEXT,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "repository" (
    "repo_id" BIGINT NOT NULL,
    "name" VARCHAR(255),
    "full_name" VARCHAR(255),
    "private" BOOLEAN,
    "html_url" TEXT,
    "description" TEXT,
    "default_branch" VARCHAR(255),
    "language" VARCHAR(255),
    "created_at" TIMESTAMP(6),
    "updated_at" TIMESTAMP(6),
    "pushed_at" TIMESTAMP(6),
    "owner_login" VARCHAR(255),

    CONSTRAINT "repository_pkey" PRIMARY KEY ("repo_id")
);

-- CreateTable
CREATE TABLE "commit" (
    "commit_sha" VARCHAR(255) NOT NULL,
    "repo_id" BIGINT,
    "author_name" VARCHAR(255),
    "author_email" VARCHAR(255),
    "date" TIMESTAMP(6),
    "message" TEXT,
    "parent_sha" VARCHAR(255),

    CONSTRAINT "commit_pkey" PRIMARY KEY ("commit_sha")
);

-- CreateTable
CREATE TABLE "file" (
    "file_id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "repo_id" BIGINT,
    "path" TEXT NOT NULL,
    "sha" VARCHAR(255),
    "size" INTEGER,
    "type" VARCHAR(50),

    CONSTRAINT "file_pkey" PRIMARY KEY ("file_id")
);

-- CreateTable
CREATE TABLE "issue" (
    "issue_id" INTEGER NOT NULL,
    "repo_id" BIGINT,
    "title" TEXT,
    "state" VARCHAR(50),
    "created_at" TIMESTAMP(6),
    "closed_at" TIMESTAMP(6),

    CONSTRAINT "issue_pkey" PRIMARY KEY ("issue_id")
);

-- CreateTable
CREATE TABLE "pull" (
    "pull_id" INTEGER NOT NULL,
    "repo_id" BIGINT,
    "title" TEXT,
    "state" VARCHAR(50),
    "created_at" TIMESTAMP(6),
    "closed_at" TIMESTAMP(6),

    CONSTRAINT "pull_pkey" PRIMARY KEY ("pull_id")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "ownerId" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProjectMember" (
    "id" SERIAL NOT NULL,
    "projectId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "role" "Role",

    CONSTRAINT "ProjectMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProjectRepository" (
    "id" SERIAL NOT NULL,
    "projectId" INTEGER NOT NULL,
    "repo_id" BIGINT NOT NULL,

    CONSTRAINT "ProjectRepository_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CodeSummary" (
    "id" SERIAL NOT NULL,
    "projectId" INTEGER NOT NULL,
    "repo_id" BIGINT,
    "runId" TEXT,
    "targetId" TEXT NOT NULL,
    "level" TEXT NOT NULL,
    "summaryText" TEXT NOT NULL,
    "modelName" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CodeSummary_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Task" (
    "id" SERIAL NOT NULL,
    "projectId" INTEGER NOT NULL,
    "repo_id" BIGINT,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "status" "TaskStatus" NOT NULL DEFAULT 'UNDONE',
    "role" "Role",
    "assigneeUserId" INTEGER,
    "source" TEXT NOT NULL DEFAULT 'AI',
    "runId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Task_pkey" PRIMARY KEY ("id")
);

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

-- CreateTable
CREATE TABLE "GraphNode" (
    "id" BIGSERIAL NOT NULL,
    "repo_id" BIGINT NOT NULL,
    "file_path" TEXT,
    "label" TEXT NOT NULL,
    "type" TEXT,
    "metadata" JSONB,

    CONSTRAINT "GraphNode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GraphEdge" (
    "id" BIGSERIAL NOT NULL,
    "repo_id" BIGINT NOT NULL,
    "from_id" BIGINT NOT NULL,
    "to_id" BIGINT NOT NULL,
    "relation" TEXT NOT NULL,
    "metadata" JSONB,

    CONSTRAINT "GraphEdge_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_githubId_key" ON "User"("githubId");

-- CreateIndex
CREATE UNIQUE INDEX "Embedding_summaryId_key" ON "Embedding"("summaryId");

-- CreateIndex
CREATE UNIQUE INDEX "ContextMeta_repo_id_key" ON "ContextMeta"("repo_id");

-- CreateIndex
CREATE UNIQUE INDEX "Graph_repo_id_key" ON "Graph"("repo_id");

-- AddForeignKey
ALTER TABLE "commit" ADD CONSTRAINT "commit_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "file" ADD CONSTRAINT "file_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "issue" ADD CONSTRAINT "issue_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "pull" ADD CONSTRAINT "pull_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectMember" ADD CONSTRAINT "ProjectMember_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectMember" ADD CONSTRAINT "ProjectMember_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectRepository" ADD CONSTRAINT "ProjectRepository_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectRepository" ADD CONSTRAINT "ProjectRepository_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeSummary" ADD CONSTRAINT "CodeSummary_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CodeSummary" ADD CONSTRAINT "CodeSummary_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Task" ADD CONSTRAINT "Task_assigneeUserId_fkey" FOREIGN KEY ("assigneeUserId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Task" ADD CONSTRAINT "Task_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Task" ADD CONSTRAINT "Task_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE SET NULL ON UPDATE CASCADE;

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

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_from_id_fkey" FOREIGN KEY ("from_id") REFERENCES "GraphNode"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_to_id_fkey" FOREIGN KEY ("to_id") REFERENCES "GraphNode"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
