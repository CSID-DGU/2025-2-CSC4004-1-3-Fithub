import { Router } from "express";
import { getMyGitHubProfile } from "../controller/userController";
import { requireAuth } from "../middleware/authMiddleware";

const router = Router();
router.get("/me", requireAuth, getMyGitHubProfile);
export default router;
