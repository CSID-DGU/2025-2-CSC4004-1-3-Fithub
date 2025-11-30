import axios from "axios";
import prisma from "../../prisma";

const AI_SERVER = process.env.AI_SERVER;

interface SummaryParams {
  filePath: string;
  content: string;
  repoId?: bigint;
  projectId?: number;
}

export const createSummary = async (params: SummaryParams) => {
  const { filePath, content, repoId, projectId } = params;

  const response = await axios.post(`${AI_SERVER}/summarize`, {
    file_name: filePath,
    content,
  });

  const data = response.data;

  const saved = await prisma.codeSummary.create({
    data: {
      projectId: projectId ?? 1,
      repo_id: repoId ?? undefined,
      targetId: filePath,
      level: "file",
      summaryText: data.unified_summary,
    },
  });

  return saved;
};

export const createSummariesBulk = async (
  summaries: { filePath: string; content: string; repoId?: bigint; projectId?: number }[]
) => {
  const results = [];

  for (const item of summaries) {
    const saved = await createSummary(item);
    results.push(saved);
  }

  return results;
};

export const getSummariesByProject = async (projectId: number) => {
  return prisma.codeSummary.findMany({
    where: { projectId },
    include: { repository: true },
  });
};
