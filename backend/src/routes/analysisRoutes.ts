import { Router } from "express";
import {
  startFullAnalysis,
  getAnalysisStatus,
  getAnalysisResult
} from "../controller/analysisController";

const router = Router();


router.post("/run", startFullAnalysis);
router.get("/status/:runId", getAnalysisStatus);
router.get("/result/:runId", getAnalysisResult);

export default router;
