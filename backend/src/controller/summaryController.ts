import { Request, Response } from "express";
import { createRepoSummaries, getSummariesByProject } from "../github/services/summaryService";

export const summarizeRepository = async (req: Request, res: Response) => {
  try {
    const { repoId, repoName, projectId } = req.body;
    if (!repoId) return res.status(400).json({ error: "repoId is required" });

    const result = await createRepoSummaries({
      repoId,
      repoName: repoName ?? "",
      projectId
    });

    return res.json({
      message: "Repository summaries created successfully",
      savedCount: result.savedCount,
      totalFilesProcessed: result.files
    });
  } catch (err: any) {
    console.error("summarizeRepository error:", err);
    return res.status(500).json({
      error: "Failed to summarize repository",
      details: err.message
    });
  }
};

export const getSummaries = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    if (isNaN(projectId)) return res.status(400).json({ error: "Invalid projectId" });

    const summaries = await getSummariesByProject(projectId);

    return res.json({
      projectId,
      totalSummaries: summaries.length,
      summaries
    });
  } catch (err: any) {
    console.error("getSummaries error:", err);
    return res.status(500).json({
      error: "Failed to get summaries",
      details: err.message
    });
  }
};
