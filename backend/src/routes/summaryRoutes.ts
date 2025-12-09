// src/routes/summaryRoutes.ts

import { Router } from "express";
import { getSummaryByRunId } from "../controller/summaryController";

const router = Router();

/**
 * GET /summary/:runId
 * runId 기반 Summary + SummaryItems 조회
 */
router.get("/:runId", getSummaryByRunId);

export default router;
