import prisma from "../../prisma";

export const recommendationService = {

  //기존 runId에 대한 recommendation 다 삭제 후 다시 저장
  async saveRecommendations(runId: string, repoId: bigint, recommendations: any[]) {
    if (!Array.isArray(recommendations)) {
      console.warn("[RECOMMENDATION] result.recommendations is not an array");
      return;
    }

    console.log(`[RECOMMENDATION] Saving ${recommendations.length} items`);

    // 1) 기존 recommendations 삭제 (같은 runId 기준)
    await prisma.recommendation.deleteMany({
      where: { runId }
    });

    // 2) 새 recommendations 저장
    const data = recommendations.map((rec: any, index: number) => ({
      runId,
      repoId,
      target: rec.target ?? null,
      reason: rec.reason ?? null,
      priority: rec.priority ?? null,
      category: rec.category ?? null,
      type: rec.type ?? null,
      confidence: rec.confidence ?? null,
      rank: rec.rank ?? index + 1,
      relatedNodes: rec.related_nodes ?? null
    }));

    await prisma.recommendation.createMany({ data });

    console.log("[RECOMMENDATION] Saved successfully");
  },


  // runId 기반 조회
  async getRecommendationsByRunId(runId: string) {
    return prisma.recommendation.findMany({
      where: { runId }
    });
  },

  async getRecommendationsByRepo(repoId: bigint) {
  return prisma.recommendation.findMany({
    where: { repoId },
    orderBy: { createdAt: "desc" }
  });
}


};
