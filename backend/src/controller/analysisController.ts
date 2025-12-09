// src/controller/analysisController.ts

import axios from "axios";
import fs from "fs";
import path from "path";
import { Request, Response } from "express";
import { summaryService } from "../github/services/summaryService";

const AI_AGENT_URL = process.env.AI_AGENT_URL || "http://localhost:8000";

// runId → repoId
const runRepoMap = new Map<string, bigint>();

// runId → status
const analysisStatus = new Map<string, string>();


/* ==========================================================
   1) POST /analysis/run
========================================================== */
export const startFullAnalysis = async (req: Request, res: Response) => {
  try {
    const { repo } = req.body;
    if (!repo || !repo.repo_id) {
      return res.status(400).json({ error: "repo.repo_id is required" });
    }

    const repoId = BigInt(repo.repo_id);

    const analyzeRes = await axios.post(`${AI_AGENT_URL}/analyze`, { repo });
    const runId = analyzeRes.data.run_id;

    runRepoMap.set(runId, repoId);
    analysisStatus.set(runId, "processing");

    return res.json({ runId });

  } catch (err) {
    console.error("[ERROR startFullAnalysis]", err);
    return res.status(500).json({ error: "Failed to start analysis" });
  }
};


/* ==========================================================
   2) GET /analysis/status/:runId
========================================================== */
export const getAnalysisStatus = async (req: Request, res: Response) => {
  try {
    const { runId } = req.params;

    const baseDir = path.join(__dirname, "../../results", runId);

    if (fs.existsSync(baseDir)) {
      analysisStatus.set(runId, "completed");
      return res.json({ status: "completed" });
    }

    return res.json({ status: "processing" });

  } catch (err) {
    return res.status(500).json({ error: "Failed to check status" });
  }
};


/* ==========================================================
   3) GET /analysis/result/:runId
      summarization.json → DB 저장만 (프론트 반환 X)
      structural.json → 프론트로 반환
========================================================== */
export const getAnalysisResult = async (req: Request, res: Response) => {
  try {
    const { runId } = req.params;
    const repoId = runRepoMap.get(runId);

    const baseDir = path.join(__dirname, "../../results", runId);

    if (!fs.existsSync(baseDir)) {
      return res.status(404).json({ error: "Result not ready" });
    }

    // ⭐ structural.json 읽기
    const structuralPath = path.join(baseDir, "structural.json");
    let structural = null;

    if (fs.existsSync(structuralPath)) {
      structural = JSON.parse(fs.readFileSync(structuralPath, "utf-8"));
    }

    // ⭐ summarization.json → DB 저장만 함
    try {
      if (repoId) {
        await summaryService.saveSummaryFromResult(runId, repoId);
        console.log("[SUMMARY] Saved to DB successfully");
      }
    } catch (err) {
      console.error("[ERROR] Failed to save summary:", err);
    }

    const summary = await summaryService.getSummaryByRunId(runId);

    //structual.json / summary(parsed)반환
    return res.json({
      runId,
      structural,
      summary,
    });

  } catch (err) {
    console.error("[ERROR getAnalysisResult]", err);
    return res.status(500).json({ error: "Failed to load analysis result" });
  }
};
