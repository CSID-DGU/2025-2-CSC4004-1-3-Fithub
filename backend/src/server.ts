import dotenv from "dotenv";
dotenv.config();

import express from "express";
import cors from "cors";
import helmet from "helmet";
import githubRoutes from "./routes/githubRoutes";
import { errorHandler } from "./middleware/errorHandler";
import projectRoutes from "./routes/projectRoutes";
import summaryRoutes from "./routes/summaryRoutes";
import taskRoutes from "./routes/taskRoutes";
import authRoutes from "./routes/authRoutes";
import graphRoutes from "./routes/graphRoutes";
import YAML from "yamljs";


(BigInt.prototype as any).toJSON = function () {
  return this.toString();
};

const app = express();

app.use(cors({
  origin: "*",   
  credentials: true
}));

app.use(helmet());
app.use(express.json());

//github oauth code를 받기 위한 리다이렉트용 dummy url -> 프론트 연동 후 삭제 예정
app.get("/auth/github/dummy", (req, res) => {
  const code = req.query.code;
  res.send(`Your GitHub code is: ${code}`);
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use("/auth", authRoutes);                 
app.use("/projects", projectRoutes);          
app.use("/summaries", summaryRoutes);
app.use("/tasks", taskRoutes);
app.use("/github", githubRoutes);
app.use("/graph",graphRoutes);
app.use(errorHandler);

app.get("/", (_req, res) => {
  res.send("Backend server is running.");
});


const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Node.js Backend server is running on port ${PORT}`);
});

console.log("current database url=", process.env.DATABASE_URL);