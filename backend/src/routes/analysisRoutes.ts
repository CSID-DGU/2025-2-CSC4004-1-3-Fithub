// src/routes/analysisRoutes.ts

import { Router } from "express";
import {
  startFullAnalysis,
  getAnalysisStatus,
  getAnalysisResult
} from "../controller/analysisController";

const router = Router();

/**
 * ============================================
 * POST /analysis/run
 * - 프론트가 repo 정보 전달
 * - 백엔드가 AI analyze 실행 → runId 반환
 * ============================================
 */
router.post("/run", startFullAnalysis);

/**
 * ============================================
 * GET /analysis/status/:runId
 * - 프론트 폴링 전용
 * - 폴더 생성 여부만 체크 (AI 서버 호출 X)
 * ============================================
 */
router.get("/status/:runId", getAnalysisStatus);

/**
 * ============================================
 * GET /analysis/result/:runId
 * - structural.json만 프론트로 전달
 * - summarization.json은 DB에 저장만 하고 반환 X
 * ============================================
 */
router.get("/result/:runId", getAnalysisResult);

export default router;
