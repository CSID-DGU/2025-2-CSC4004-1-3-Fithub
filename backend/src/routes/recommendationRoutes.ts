import { Router } from "express";
import { getRecommendationsByRepo } from "../controller/recommendationController";

const router = Router();

// GET /analysis/recommendations/:repoId
router.get("/:repoId", getRecommendationsByRepo);

export default router;
