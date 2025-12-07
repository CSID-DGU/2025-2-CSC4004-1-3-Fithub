import { Router } from "express";
import {summarizeRepository, getSummaries} from "../controller/summaryController";

import { requireAuth } from "../middleware/authMiddleware";
import { requireProjectMember } from "../middleware/projectAuth";

const router = Router();

router.post("/",requireAuth,summarizeRepository);
router.get("/:projectId",requireAuth,requireProjectMember,getSummaries);
export default router;
