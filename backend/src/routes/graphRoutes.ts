import { Router } from "express";
import { uploadGraph, fetchGraph } from "../controller/GraphController";
import { requireAuth } from "../middleware/authMiddleware";

const router = Router();

router.post("/", requireAuth, uploadGraph);//그래프 저장
router.get("/:repoId", requireAuth, fetchGraph);//그래프 조회

export default router;
