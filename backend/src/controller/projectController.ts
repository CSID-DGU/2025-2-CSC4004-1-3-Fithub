import { Request, Response } from "express";
import * as projectService from "../github/services/projectService";
import { AuthRequest } from "../middleware/authMiddleware";
import prisma from "../prisma";
import * as githubService from "../github/githubService";   

export const createProject = async (req: AuthRequest, res: Response) => {
  try {
<<<<<<< HEAD
    const userId = req.user!.id;
=======
>>>>>>> be3bd69 (edited: authorization , project role , db prisma)
    const { name, description } = req.body;

    //check JWT authorization
    if (!req.user || !req.user.id) {
      return res.status(401).json({
        error: "Unauthorized: JWT가 필요합니다.",
      });
    }

    //ownerId <-JWT
    const ownerId = req.user.id;

    const project = await projectService.createProject({
      name,
      description,
      ownerId,
    });

    return res.json(project);
  } catch (err) {
    console.error("Create project error:", err);
    return res.status(500).json({ error: "Failed to create project" });
  }
};

//get Project detail
export const getProjectById = async (req: Request, res: Response) => {
  try {
    const result = await projectService.getProjectById(
      Number(req.params.projectId)
    );
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: "Failed to get project" });
  }
};

<<<<<<< HEAD
import { dbService } from "../github/services/dbService";
import { AIService } from "../services/aiService";

//add repository to Project
export const addRepoToProject = async (req: Request, res: Response) => {
  try {
    const result = await projectService.addRepoToProject(
      Number(req.params.projectId),
      BigInt(req.body.repo_id)
    );

    // Trigger AI Analysis asynchronously
    const repoId = String(req.body.repo_id);
    dbService.getRepo(repoId).then(async (repo) => {
      if (repo && repo.full_name) {
        const repoUrl = `https://github.com/${repo.full_name}`;
        console.log(`Triggering AI analysis for ${repoUrl}...`);
        try {
          const runId = await AIService.analyzeRepository(repoUrl);
          console.log(`Analysis started with Run ID: ${runId}`);

          // Poll for results (optional, or just let it run)
          // In a real app, you might want to store runId in DB
          AIService.pollAnalysisResult(runId)
            .then(result => console.log(`Analysis completed for ${repoUrl}:`, result.status))
            .catch(err => console.error(`Analysis polling failed for ${repoUrl}:`, err));

        } catch (error) {
          console.error(`Failed to trigger analysis for ${repoUrl}:`, error);
        }
      }
    }).catch(err => console.error("Failed to fetch repo info for analysis:", err));
=======
//add github repository to project
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
>>>>>>> be3bd69 (edited: authorization , project role , db prisma)

    res.json(result);
  } catch (err) {
    console.error("Add repo error:", err);
    res.status(500).json({ error: "Failed to add repository to project" });
  }
};

//add member to Project (owner)
export const addProjectMember = async (req: AuthRequest, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const { userId } = req.body;

    if (!userId) {
      return res.status(400).json({ error: "userId is required" });
    }

    const newMember = await projectService.addMemberToProject(
      projectId,
      Number(userId)
    );

    res.json(newMember);
  } catch (err) {
    console.error("Add member error:", err);
    res.status(500).json({ error: "Failed to add member" });
  }
};

//get Project Members
export const getProjectMembers = async (req: AuthRequest, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const members = await projectService.getProjectMembers(projectId);
    res.json(members);
  } catch (err) {
    console.error("Get members error:", err);
    res.status(500).json({ error: "Failed to get project members" });
  }
};

//delete Project Members (owner)
export const removeProjectMember = async (req: AuthRequest, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const userId = Number(req.params.userId);

    const deleted = await projectService.removeProjectMember(projectId, userId);

    if (deleted.count === 0) {
      return res.status(404).json({ error: "Member not found in project" });
    }

    res.json({ message: "Member removed successfully" });
  } catch (err) {
    console.error("Remove member error:", err);
    res.status(500).json({ error: "Failed to remove member" });
  }
};


//get project role list
export const getUserRoles = (req: Request, res: Response) => {
  const roles=projectService.getRoles();
  res.json(roles);
};

//update project roles
export const updateProjectMemberRole = async (req: AuthRequest, res: Response) => {
  try {
    const { projectId, memberId } = req.params;
    const { role } = req.body;

    const updated = await projectService.updateProjectMemberRole(
      Number(projectId),
      Number(memberId),
      role
    );

    res.status(200).json(updated);
  } catch (err:any) {
    res.status(500).json({ error: err.message });
  }
};

<<<<<<< HEAD
//chooese project roles
export const setProjectMemberRole = async (req: AuthRequest, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const userId = req.user!.id;
    const { role_id } = req.body;

    if (!role_id) {
      return res.status(400).json({ error: "role_id is required" });
    }

    const member = await prisma.projectMember.findFirst({
      where: { userId, projectId }
    });

    if (!member) {
      return res.status(403).json({ error: "Not a project member" });
    }

    await prisma.projectMember.update({
      where: { id: member.id },
      data: { role_id }
    });

    res.json({ message: "Role updated successfully" });

  } catch (err) {
    console.error("Set project role error:", err);
    res.status(500).json({ error: "Failed to set role" });
  }
};
=======
>>>>>>> be3bd69 (edited: authorization , project role , db prisma)
