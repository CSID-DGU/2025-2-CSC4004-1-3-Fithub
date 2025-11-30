import { Router } from "express";
import {
  createGraphController,
  getGraphController,
} from "../controller/GraphController";

const router = Router();

router.post("/generate", createGraphController);
router.get("/:repoId", getGraphController);

export default router;
