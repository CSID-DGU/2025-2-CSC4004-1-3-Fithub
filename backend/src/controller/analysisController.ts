//현재 문제:task_output.json 파일이 반환되지 않음 -> json 파일을 잘 읽어오는지 여부 test가 안 됨
//structural.json: 그래프 정보 , summarization.json: 요약 정보 , task_output.json: task 정보

import axios from "axios";
import fs from "fs";
import path from "path";
import { Request, Response } from "express";
import { summaryService } from "../github/services/summaryService";
import { taskService } from "../github/services/taskService";

const AI_AGENT_URL = process.env.AI_AGENT_URL || "http://localhost:8000";

const runRepoMap = new Map<string, bigint>();
const runProjectMap = new Map<string, number>();
const analysisStatus = new Map<string, string>();


// POST /analysis/run : AI 분석 시작
export const startFullAnalysis = async (req: Request, res: Response) => {
  console.log("START ANALYSIS");

  try {
    const { repo, projectId } = req.body;
    if (!repo?.repo_id) return res.status(400).json({ error: "repo.repo_id is required" });
    if (!projectId) return res.status(400).json({ error: "projectId is required" });

    const repoId = BigInt(repo.repo_id);
    console.log("repoId:", repoId, "projectId:", projectId);

    const analyzeRes = await axios.post(`${AI_AGENT_URL}/analyze`, { repo });
    const runId = analyzeRes.data.run_id;
    console.log("runId:", runId);

    runRepoMap.set(runId, repoId);
    runProjectMap.set(runId, projectId);
    analysisStatus.set(runId, "processing");

    return res.json({ runId });

  } catch (err: any) {
    console.error("ERROR startFullAnalysis:", err.message);
    return res.status(500).json({ error: "Failed to start analysis" });
  }
};



// GET /analysis/status/:runId : 모든 json이 생성되었는지 확인
export const getAnalysisStatus = async (req: Request, res: Response) => {
  console.log("CHECK STATUS");

  try {
    const { runId } = req.params;
    //results 파일 경로: backend/results
    const baseDir = path.join(__dirname, "../../../results", runId);

    //structural.json: 그래프 정보 , summarization.json: 요약 정보 , task_output.json: task 정보
    const structural = path.join(baseDir, "structural.json");
    const summary = path.join(baseDir, "summarization.json");
    const tasks = path.join(baseDir, "task_output.json");

    const hasStructural = fs.existsSync(structural);
    const hasSummary = fs.existsSync(summary);
    const hasTasks = fs.existsSync(tasks);

    //세 파일이 모두 생성되어야 완료되었다고 판단한다.
    if (hasStructural && hasSummary && hasTasks) {
      console.log("STATUS completed");
      return res.json({ status: "completed" });
    }

    console.log("STATUS processing");
    return res.json({
      status: "processing",
      structural: hasStructural,
      summarization: hasSummary,
      task_recommendation: hasTasks
    });

  } catch (err) {
    console.error("ERROR getAnalysisStatus:", err);
    return res.status(500).json({ error: "Failed to check status" });
  }
};

// GET /analysis/result/:runId : 결과 조회
export const getAnalysisResult = async (req: Request, res: Response) => {
  console.log("LOAD RESULT");

  try {
    const { runId } = req.params;

    const repoId = runRepoMap.get(runId);
    const projectId = runProjectMap.get(runId);

    if (!repoId || !projectId) return res.status(400).json({ error: "Invalid runId mapping" });

    const baseDir = path.join(__dirname, "../../../results", runId);
    const structuralPath = path.join(baseDir, "structural.json");
    const summaryPath = path.join(baseDir, "summarization.json");
    const tasksPath = path.join(baseDir, "task_output.json");

    const ready = fs.existsSync(structuralPath) && fs.existsSync(summaryPath) && fs.existsSync(tasksPath);
    if (!ready) {
      console.log("RESULT not ready");
      return res.json({ status: "processing" });
    }

    const structural = JSON.parse(fs.readFileSync(structuralPath, "utf-8"));

    await summaryService.saveSummaryFromResult(runId, repoId);
    await taskService.saveTasksFromResult(runId, repoId, projectId);

    const summary = await summaryService.getSummaryByRunId(runId);
    const tasks = await taskService.getTasksByRunId(runId);

    return res.json({
      runId,
      status: "completed",
      structural, //json 그대로 반환
      summary, //db 저장 후 반환
      tasks //db 저장 후 반환
    });

  } catch (err: any) {
    console.error("ERROR getAnalysisResult:", err.message);
    return res.status(500).json({ error: "Failed to load result" });
  }
};
