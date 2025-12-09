import { Router } from "express";
import { 
  createProject, getProjectById, addRepoToProject, addProjectMember,
  getProjectMembers, removeProjectMember, getUserRoles, updateProjectMemberRole,
  deleteProject, removeRole
} from "../controller/projectController";
import { requireAuth } from "../middleware/authMiddleware";
import { requireProjectOwner } from "../middleware/projectAuth";
import { Request, Response } from "express";
import * as projectService from "../github/services/projectService";

const router = Router();


// Create Project
router.post("/", requireAuth, createProject);


// Get Project List
router.get("/lists", requireAuth, async (req: Request, res: Response) => {
  try {
    const projects = await projectService.getProjectLists();
    return res.json(projects);

  } catch (err: any) {

    if (err.code?.startsWith("P")) {
      return res.status(500).json({
        error: "Database Error",
        message: err.meta?.cause || err.message
      });
    }

    if (err.message?.includes("ECONNREFUSED") || err.code === "ECONNREFUSED") {
      return res.status(503).json({
        error: "Service Unavailable",
        message: "Database connection failed"
      });
    }

    if (err instanceof SyntaxError) {
      return res.status(400).json({
        error: "Bad Request",
        message: "Invalid JSON format"
      });
    }

    return res.status(500).json({
      error: "Internal Server Error",
      message: err.message || "Failed to fetch project lists"
    });
  }
});


// Project Detail
router.get("/:projectId", requireAuth, requireProjectOwner, getProjectById);


// Repo → Project Add
router.post("/:projectId/repos", addRepoToProject);


// Role 조회
router.get("/roles", requireAuth, getUserRoles);


// Delete Project
router.delete("/:projectId", requireAuth, deleteProject);


// Members CRUD
router.post("/:projectId/members", requireAuth, requireProjectOwner, addProjectMember);
router.get("/:projectId/members", requireAuth, getProjectMembers);
router.delete("/:projectId/members/:userId", requireAuth, requireProjectOwner, removeProjectMember);


// Role Update / Remove
router.patch("/:projectId/members/:memberId/role", requireAuth, requireProjectOwner, updateProjectMemberRole);
router.delete("/:projectId/members/:userId/role/:role", requireAuth, removeRole);

export default router;
