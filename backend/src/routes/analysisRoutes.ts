import { Router } from "express";
import {
  startFullAnalysis,
  getAnalysisStatus,
  getAnalysisResult
} from "../controller/analysisController";

const router = Router();

//run
router.post("/run", startFullAnalysis);

//run 상태반환
router.get("/status/:runId", getAnalysisStatus);

//run 결과반환
router.get("/result/:runId", getAnalysisResult);

export default router;
