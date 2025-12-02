import { Router } from "express";
import { createProject, getProjectById, addRepoToProject, addProjectMember, getProjectMembers,removeProjectMember,getUserRoles,updateProjectMemberRole,deleteProject,removeRole } from "../controller/projectController";
import { requireAuth } from "../middleware/authMiddleware";
import { requireProjectOwner } from "../middleware/projectAuth";
import { Request, Response } from "express";
import * as projectService from "../github/services/projectService";


const router = Router();
router.post("/", requireAuth, createProject);

router.get("/lists", requireAuth, async (req: Request, res: Response) => {
    console.log("[PROJECT LIST API] Request received");

  try {
    const projects = await projectService.getProjectLists();
    console.log("[PROJECT LIST API] Success:", projects.length, "projects");
    return res.json(projects);

  } catch (err: any) {
    console.error("[PROJECT LIST API ERROR]:", err);

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


router.get("/:projectId", requireAuth, requireProjectOwner,getProjectById);
router.post("/:projectId/repos", addRepoToProject);
router.get("/roles", requireAuth, getUserRoles);
router.delete("/:projectId", requireAuth, deleteProject);
router.post("/:projectId/members", requireAuth, requireProjectOwner, addProjectMember);
router.get("/:projectId/members", requireAuth, getProjectMembers);
router.delete("/:projectId/members/:userId", requireAuth, requireProjectOwner, removeProjectMember);
router.patch("/:projectId/members/:memberId/role", requireAuth, requireProjectOwner, updateProjectMemberRole);
router.delete("/:projectId/members/:userId/role/:role", requireAuth, removeRole);

export default router;

