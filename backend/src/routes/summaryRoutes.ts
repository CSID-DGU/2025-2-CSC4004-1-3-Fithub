import { Router } from "express";
import { getSummaryByRunId } from "../controller/summaryController";

const router = Router();

//summary 조회
router.get("/:runId", getSummaryByRunId);

export default router;
