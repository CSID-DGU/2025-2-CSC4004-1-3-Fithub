import { Router } from "express";
import { createProject, getProjectById, addRepoToProject, addProjectMember, getProjectMembers,removeProjectMember } from "../controller/projectController";
import { requireAuth } from "../middleware/authMiddleware";
import { requireProjectOwner } from "../middleware/projectAuth";

const router = Router();

router.post("/", requireAuth, createProject);
router.get("/:projectId", requireAuth,requireProjectOwner,getProjectById);
router.post("/:projectId/repos", addRepoToProject);
router.post("/:projectId/members",requireAuth,requireProjectOwner,addProjectMember); //멤버 추가(owner만)
router.get("/:projectId/members", requireAuth, getProjectMembers); //멤버 조회(누구나)
router.delete("/:projectId/members/:userId",requireAuth,requireProjectOwner,removeProjectMember); //멤버 삭제(owner만)
export default router;
