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

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_from_id_fkey" FOREIGN KEY ("from_id") REFERENCES "GraphNode"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GraphEdge" ADD CONSTRAINT "GraphEdge_to_id_fkey" FOREIGN KEY ("to_id") REFERENCES "GraphNode"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
