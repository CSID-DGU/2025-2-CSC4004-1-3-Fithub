import { Router } from "express";
import {
  createSummaries,
  getSummaries,
} from "../controller/summaryController";

import { requireAuth } from "../middleware/authMiddleware";
import { requireProjectMember } from "../middleware/projectAuth";

const router = Router();

router.post("/", requireAuth, createSummaries);
router.get("/:projectId", requireAuth, requireProjectMember, getSummaries);

export default router;
