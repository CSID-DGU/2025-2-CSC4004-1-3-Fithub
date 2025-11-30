import axios from "axios";
import prisma from "../../prisma";

const AI_SERVER = process.env.AI_SERVER;

const getRoleIdFromName = async (roleName: string | null | undefined) => {
  if (!roleName) return null;

  const role = await prisma.role.findUnique({
    where: { name: roleName },
  });

  return role?.id ?? null;
};

export const requestAITasks = async (params: any) => {
  const response = await axios.post(`${AI_SERVER}/task`, params);
  return response.data.tasks;
};

export const saveTasks = async (tasksFromAI: any[]) => {
  const savedTasks = [];

  for (const t of tasksFromAI) {
    const role_id = await getRoleIdFromName(t.role);

    const saved = await prisma.task.create({
      data: {
        title: t.title,
        description: t.description,
        projectId: t.projectId,
        repo_id: t.repoId ? BigInt(t.repoId) : null,
        role_id: role_id,
        source: "AI",
      },
    });

    savedTasks.push(saved);
  }

  return savedTasks;
};

export const getTasksForUserRole = async (roleId: number) => {
  return await prisma.task.findMany({
    where: { role_id: roleId },
  });
};

export const getTasksByProject = async (projectId: number) => {
  return await prisma.task.findMany({
    where: { projectId },
  });
};
