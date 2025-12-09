import prisma from "../../prisma";
import fs from "fs";
import path from "path";

// category → role ENUM 매핑
function mapCategoryToRole(category?: string) {
  if (!category) return "COMMON";

  const key = category.toLowerCase();
  if (key.includes("backend")) return "BACKEND";
  if (key.includes("frontend")) return "FRONTEND";
  if (key.includes("ai")) return "AI";
  if (key.includes("devops")) return "DEVOPS";
  if (key.includes("database")) return "DATABASE";

  return "COMMON";
}

export const taskService = {
  //task_output.json -> db 저장
  async saveTasksFromResult(runId: string, repoId: bigint, projectId: number) {
    const baseDir = path.join(__dirname, "../../../results", runId);
    const taskFile = path.join(baseDir, "task_output.json");

    if (!fs.existsSync(taskFile)) {
      console.log("[TASK] No task_output.json found → skipping");
      return;
    }

    const json = JSON.parse(fs.readFileSync(taskFile, "utf-8"));
    const recommendations = json.recommendations || [];

    const tasks = recommendations.map((rec: any) => ({
      projectId,
      repo_id: repoId,

      //매핑
      title: `${rec.type.toUpperCase()}: ${rec.target}`,
      description: rec.reason || null,
      target: rec.target || null,
      priority: rec.priority || null,
      taskType: rec.type || null,
      category: rec.category || null,
      confidence: rec.confidence || null,

      //role 자동 매핑
      role: mapCategoryToRole(rec.category),

      source: "AI",
      runId,
    }));

    await prisma.task.createMany({ data: tasks });

    console.log(`[TASK] Saved ${tasks.length} AI tasks to DB.`);
  },

  //task 조회
  async getTasksByRunId(runId: string) {
    return prisma.task.findMany({
      where: { runId },
      orderBy: { id: "asc" }
    });
  }
};
