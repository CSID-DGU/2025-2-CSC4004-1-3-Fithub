import axios from "axios";
import prisma from "../../prisma";

const AI_SERVER = process.env.AI_SERVER;

interface GraphNode {
  id: string;
  type: string;
  summary?: string;
  summary_details?: {
    logic?: string;
    intent?: string;
    structure?: string;
  };
}

interface RepoAnalysisResponse {
  graph: {
    nodes: GraphNode[];
    edges: any[];
  };
}

interface RepoSummaryParams {
  repoId: bigint | number;
  projectId?: number;
  repoName?: string;
}

export const createRepoSummaries = async (params: RepoSummaryParams) => {
  const { repoId, projectId, repoName } = params;

  if (!AI_SERVER) throw new Error("AI_SERVER not set");

  const { data } = await axios.post<RepoAnalysisResponse>(`${AI_SERVER}/summarize/repo`, {
    repo: { repo_id: String(repoId), name: repoName ?? "" },
    options: {},
    thresholds: { consistency_min: 0.7, retry_max: 2 }
  });

  if (!data.graph?.nodes) throw new Error("AI response missing graph.nodes");

  const fileNodes = data.graph.nodes.filter((n) => n.type === "file");

  const extractSummary = (node: GraphNode): string =>
    node.summary ||
    node.summary_details?.logic ||
    node.summary_details?.intent ||
    node.summary_details?.structure ||
    "";

  const saved = await prisma.codeSummary.createMany({
    data: fileNodes.map((node) => ({
      projectId: projectId ?? 1,
      repo_id: BigInt(repoId),
      summaryText: extractSummary(node),
      runId: null,
      modelName: null
    }))
  });

  return { savedCount: saved.count, files: fileNodes.length };
};

export const getSummariesByProject = async (projectId: number) => {
  return prisma.codeSummary.findMany({
    where: { projectId },
    include: { repository: true }
  });
};
