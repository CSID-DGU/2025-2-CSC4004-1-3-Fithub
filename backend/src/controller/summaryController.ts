import { Request, Response } from "express";
import { 
  createSummariesBulk,
  getSummariesByProject 
} from "../github/services/summaryService";


export const createSummaries = async (req: Request, res: Response) => {
  try {
    const summaries = req.body.summaries;

    if (!summaries || !Array.isArray(summaries)) {
      return res.status(400).json({ error: "summaries array is required" });
    }

    const result = await createSummariesBulk(summaries);

    res.json({
      message: "Summaries created",
      result,
    });
  } catch (err) {
    console.error("create summaries error:", err);
    res.status(500).json({ error: "Failed to create summaries" });
  }
};

export const getSummaries = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const summaries = await getSummariesByProject(projectId);
    res.json(summaries);
  } catch (err) {
    console.error("Get summaries error:", err);
    res.status(500).json({ error: "Failed to get summaries" });
  }
};
