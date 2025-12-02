import { Request, Response } from "express";
import * as projectService from "../github/services/projectService";
import { AuthRequest } from "../middleware/authMiddleware";
import prisma from "../prisma";
import * as githubService from "../github/githubService";
import { Role } from "@prisma/client"; 

//Create Project

export const createProject = async (req: AuthRequest, res: Response) => {
  try {
    const { name, description } = req.body;
    const ownerId = req.user!.id;

    const project = await prisma.project.create({
      data: {
        name,
        description,
        ownerId,
      },
    });

    res.json(project);
  } catch (err) {
    console.error("Create project error:", err);
    res.status(500).json({ error: "Failed to create project" });
  }
};

//Get Project Detail

export const getProjectById = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const project = await prisma.project.findUnique({
      where: { id: projectId },
      include: {
        members: true,
        repos: true,
      },
    });

    if (!project) return res.status(404).json({ error: "Project not found" });

    res.json(project);
  } catch (err) {
    console.error("Get project error:", err);
    res.status(500).json({ error: "Failed to load project" });
  }
};

//Add Repository To Project
export const addRepoToProject = async (req: Request, res: Response) => {
  try {
    const { owner, repo, token } = req.body;
    const projectId = Number(req.params.projectId);

    const githubRepo = await githubService.getRepoInfo(owner, repo, token);

    const result = await projectService.addRepoToProject(projectId, {
      id: BigInt(githubRepo.id),
      name: githubRepo.name,
      full_name: githubRepo.full_name,
      html_url: githubRepo.html_url,
    });

    res.json(result);
  } catch (err) {
    console.error("Add repo error:", err);
    res.status(500).json({ error: "Failed to add repository to project" });
  }
};


//Add Project Member
export const addProjectMember = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const { userId } = req.body;

    const member = await prisma.projectMember.create({
      data: {
        projectId,
        userId,
      },
    });

    res.json(member);
  } catch (err) {
    console.error("Add member error:", err);
    res.status(500).json({ error: "Failed to add member" });
  }
};

//Get Project Members

export const getProjectMembers = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const members = await prisma.projectMember.findMany({
      where: { projectId },
      include: { user: true },
    });

    res.json(members);
  } catch (err) {
    console.error("Get members error:", err);
    res.status(500).json({ error: "Failed to retrieve members" });
  }
};

//Remove Project Member

export const removeProjectMember = async (req: Request, res: Response) => {
  try {
    const memberId = Number(req.params.userId); 

    await prisma.projectMember.delete({
      where: { id: memberId },
    });

    res.json({ message: "Member removed" });
  } catch (err) {
    console.error("Remove member error:", err);
    res.status(500).json({ error: "Failed to remove member" });
  }
};

//Get Available Roles (Enum Role)
export const getUserRoles = async (req: Request, res: Response) => {
  try {
    const roles = Object.values(Role); // ⭐ 올바른 Enum 사용
    res.json(roles);
  } catch (err) {
    console.error("Get roles error:", err);
    res.status(500).json({ error: "Failed to load roles" });
  }
};

//Update Role for Member
export const updateProjectMemberRole = async (req: Request, res: Response) => {
  try {
    const memberId = Number(req.params.memberId);
    const { role } = req.body;

    const updated = await prisma.projectMember.update({
      where: { id: memberId },
      data: { role },
    });

    res.json(updated);
  } catch (err) {
    console.error("Update role error:", err);
    res.status(500).json({ error: "Failed to update role" });
  }
};
