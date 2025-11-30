import { Request, Response, NextFunction } from "express";
import prisma from "../prisma";
import { AuthRequest } from "./authMiddleware";

//프로젝트 owner인지 여부 확인
export const requireProjectOwner = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const userId = req.user?.id;
  const projectId = Number(req.params.projectId);

  if (!userId) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  const project = await prisma.project.findUnique({
    where: { id: projectId },
  });

  if (!project) {
    return res.status(404).json({ error: "Project not found" });
  }

  if (project.ownerId !== userId) {
    return res.status(403).json({ error: "Only owner can modify members" });
  }
  next();
};

//프로젝트 멤버인지 여부 확인
export const requireProjectMember = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const userId = req.user?.id;
  const projectId = Number(req.params.projectId);

  if (!userId) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  //이 프로젝트에 userId가 멤버로 존재하는지 여부 확인
  const membership = await prisma.projectMember.findFirst({
    where: {
      projectId,
      userId,
    },
  });
  if (!membership) {
    return res.status(403).json({ error: "Access denied: not a project member" });
  }
  next();
};