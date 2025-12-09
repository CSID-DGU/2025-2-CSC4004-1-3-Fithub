import { Request, Response } from "express";
import { summaryService } from "../github/services/summaryService";

//summary 조회
export const getSummaryByRunId = async (req: Request, res: Response) => {
  try {
    const { runId } = req.params;

    if (!runId) {
      return res.status(400).json({ error: "runId is required" });
    }

    const summary = await summaryService.getSummaryByRunId(runId);

    if (!summary) {
      return res.status(404).json({ error: "Summary not found" });
    }

    return res.json(summary);

  } catch (err) {
    console.error("[ERROR] getSummaryByRunId:", err);
    return res.status(500).json({ error: "Failed to load summary" });
  }

};
