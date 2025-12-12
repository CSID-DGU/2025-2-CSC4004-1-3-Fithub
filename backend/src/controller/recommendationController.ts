import { Request, Response } from "express";
import { recommendationService } from "../github/services/recommendationService";

export const getRecommendationsByRepo = async (req: Request, res: Response) => {
  try {
    const { repoId } = req.params;

    if (!repoId) {
      return res.status(400).json({ error: "repoId is required" });
    }

    const repoIdBigInt = BigInt(repoId);

    const recommendations = await recommendationService.getRecommendationsByRepo(repoIdBigInt);

    return res.json({
      repoId,
      recommendations
    });

  } catch (err: any) {
    console.error("ERROR getRecommendationsByRepo:", err.message);
    return res.status(500).json({
      error: "Failed to load recommendations",
      details: err.message
    });
  }
};
