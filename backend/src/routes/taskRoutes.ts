import { Router } from "express";
import { getTasksByRunId } from "../controller/taskController";

const router = Router();

//task 조회
router.get("/:runId", getTasksByRunId);

export default router;
