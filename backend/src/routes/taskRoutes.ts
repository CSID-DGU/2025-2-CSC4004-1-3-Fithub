import { Router } from "express";
import { requireAuth } from "../middleware/authMiddleware";
import {
  generateTasks,
  getTasksByProjectController,
  getTasksByMyRole,
} from "../controller/taskController";

const router = Router();

router.post("/generate", generateTasks);
router.get("/:projectId", getTasksByProjectController);

router.get("/:projectId/my-role", requireAuth, getTasksByMyRole);

export default router;
