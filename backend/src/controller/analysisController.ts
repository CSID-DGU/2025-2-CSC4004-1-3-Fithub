import axios from "axios";
import fs from "fs";
import path from "path";
import { Request, Response } from "express";
import { summaryService } from "../github/services/summaryService";

const AI_AGENT_URL = process.env.AI_AGENT_URL || "http://localhost:8000";


// POST /analysis/run
export const startFullAnalysis = async (req: Request, res: Response) => {
  console.log("START ANALYSIS");

  try {
    const { repo } = req.body;

    if (!repo?.repo_id) {
      return res.status(400).json({ error: "repo.repo_id is required" });
    }

    const analyzeRes = await axios.post(`${AI_AGENT_URL}/analyze`, { repo });
    const runId = analyzeRes.data.run_id;

    console.log("[RUN START] runId =", runId);

    return res.json({ runId });

  } catch (err: any) {
    console.error("ERROR startFullAnalysis:", err.message);
    return res.status(500).json({ error: "Failed to start analysis" });
  }
};



// GET /analysis/status/:runId
export const getAnalysisStatus = async (req: Request, res: Response) => {
  console.log("CHECK STATUS");

  try {
    const { runId } = req.params;

    const baseDir = path.join(__dirname, "../../../results", runId);
    const structural = path.join(baseDir, "structural.json");
    const summary = path.join(baseDir, "summarization.json");

    const hasStructural = fs.existsSync(structural);
    const hasSummary = fs.existsSync(summary);

    console.log("[STATUS CHECK]", { hasStructural, hasSummary });

    if (hasStructural && hasSummary) {
      return res.json({ status: "completed" });
    }

    return res.json({
      status: "processing",
      structural: hasStructural,
      summarization: hasSummary
    });

  } catch (err: any) {
    console.error("ERROR getAnalysisStatus:", err.message);
    return res.status(500).json({ error: "Failed to check status" });
  }
};



// GET /analysis/result/:runId
// GET /analysis/result/:runId
export const getAnalysisResult = async (req: Request, res: Response) => {
  console.log("LOAD RESULT");

  try {
    const { runId } = req.params;
    const { repoId } = req.query;

    if (!repoId) {
      return res.status(400).json({ error: "repoId is required in query" });
    }

    const repoIdBigInt = BigInt(repoId as string);

    console.log("[AI REQUEST] GET /result/" + runId);

    // 1) 상태는 Agent에게 확인 (completed 여부 판단만)
    const aiRes = await axios.get(`${AI_AGENT_URL}/result/${runId}`);
    const aiData = aiRes.data;

    console.log("[AI RESPONSE]", aiData.status);

    if (aiData.status !== "completed") {
      return res.json({ status: "processing" });
    }

    // -----------------------------------------
    // 2) 백엔드가 직접 JSON 파일 읽기
    // -----------------------------------------
    const baseDir = path.join(process.cwd(), "results", runId);

    const structuralPath = path.join(baseDir, "structural.json");
    const summaryPath = path.join(baseDir, "summarization.json");

    console.log("[READ FILES FROM]", baseDir);

    if (!fs.existsSync(structuralPath) || !fs.existsSync(summaryPath)) {
      console.log("[FILE MISSING]");
      return res.json({ status: "processing", message: "Files not ready" });
    }

    // 파일을 실제로 읽어오기
    const structural = JSON.parse(fs.readFileSync(structuralPath, "utf-8"));
    const summarizationArray = JSON.parse(fs.readFileSync(summaryPath, "utf-8"));

    console.log("[FILE LOADED] structural + summarization");

    // -----------------------------------------
    // 3) DB 저장
    // -----------------------------------------
    console.log("[SAVE SUMMARY]");
    await summaryService.saveSummaryFromAI(runId, repoIdBigInt, summarizationArray);

    const summaryFromDB = await summaryService.getSummaryByRunId(runId);

    // -----------------------------------------
    // 4) 최종 응답
    // -----------------------------------------
    console.log("[RESULT READY]", { runId });

    return res.json({
      runId,
      status: "completed",
      structural,
      summary: summaryFromDB,
    });

  } catch (err: any) {
    console.error("ERROR getAnalysisResult:", err.message);
    return res.status(500).json({
      error: "Failed to load result",
      details: err.message
    });
  }
};
