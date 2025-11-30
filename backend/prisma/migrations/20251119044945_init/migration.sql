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

-- AddForeignKey
ALTER TABLE "commit" ADD CONSTRAINT "commit_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "file" ADD CONSTRAINT "file_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "issue" ADD CONSTRAINT "issue_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "pull" ADD CONSTRAINT "pull_repo_id_fkey" FOREIGN KEY ("repo_id") REFERENCES "repository"("repo_id") ON DELETE CASCADE ON UPDATE NO ACTION;
