// src/services/summaryService.ts

import fs from "fs";
import path from "path";
import prisma from "../../prisma";

// summarization.json의 단일 아이템 구조 타입
interface SummaryItemRaw {
  code_id?: string;
  text?: string;
  unified_summary?: string;
  level?: string;
  quality_score?: number;
  expert_views?: {
    logic?: string;
    intent?: string;
    structure?: string;
  };
}

export const summaryService = {

  /* ==========================================================
     1) summarization.json → Summary + SummaryItem 저장
  ========================================================== */
  async saveSummaryFromResult(runId: string, repoId: bigint) {
    try {
      console.log("=================================================");
      console.log("[SUMMARY] saveSummaryFromResult()");
      console.log(" runId =", runId, ", repoId =", repoId);
      console.log("=================================================");

      // 1) summarization.json 파일 경로
      const baseDir = path.join(__dirname, "../../results", runId);
      const summaryPath = path.join(baseDir, "summarization.json");

      if (!fs.existsSync(summaryPath)) {
        throw new Error(`summarization.json not found for runId=${runId}`);
      }

      // 2) summarization.json 읽기
      const raw = JSON.parse(fs.readFileSync(summaryPath, "utf-8"));

      if (!Array.isArray(raw)) {
        throw new Error("summarization.json must contain an array of items");
      }

      console.log(`[SUMMARY] Loaded ${raw.length} summary items`);

      // 3) Summary 생성 (runId + repoId)
      const summary = await prisma.summary.create({
        data: {
          runId,
          repoId
        },
      });

      console.log("[SUMMARY] Created Summary ID =", summary.id);

      // 4) SummaryItem 생성 (배열 매핑)
      const itemsData = raw.map((item: SummaryItemRaw) => ({
        summaryId: summary.id,
        codeId: item.code_id || null,
        text: item.text || null,
        unifiedSummary: item.unified_summary || null,
        level: item.level || null,
        qualityScore: item.quality_score || null,
        logic: item.expert_views?.logic || null,
        intent: item.expert_views?.intent || null,
        structure: item.expert_views?.structure || null,
      }));

      await prisma.summaryItem.createMany({ data: itemsData });

      console.log("[SUMMARY] SummaryItem 저장 개수 =", itemsData.length);

      return {
        summaryId: summary.id,
        items: itemsData.length,
      };

    } catch (err) {
      console.error("[SUMMARY SERVICE ERROR] saveSummaryFromResult:", err);
      throw err;
    }
  },

  /* ==========================================================
     2) runId로 Summary + Items 조회
  ========================================================== */
  async getSummaryByRunId(runId: string) {
    return prisma.summary.findUnique({
      where: { runId },
      include: { items: true },
    });
  },

  /* ==========================================================
     3) repoId 기준 최신 Summary
  ========================================================== */
  async getLatestSummary(repoId: bigint) {
    return prisma.summary.findFirst({
      where: { repoId },
      orderBy: { createdAt: "desc" },
      include: { items: true },
    });
  },

  /* ==========================================================
     4) repoId 기준 전체 Summary
  ========================================================== */
  async getAllSummaries(repoId: bigint) {
    return prisma.summary.findMany({
      where: { repoId },
      orderBy: { createdAt: "desc" },
      include: { items: true },
    });
  },
};
