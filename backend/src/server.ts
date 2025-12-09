import dotenv from "dotenv";
dotenv.config();

import express from "express";
import cors from "cors";
import helmet from "helmet";
import githubRoutes from "./routes/githubRoutes";
import { errorHandler } from "./middleware/errorHandler";
import projectRoutes from "./routes/projectRoutes";
import analysisRoutes from "./routes/analysisRoutes";
import summaryRoutes from "./routes/summaryRoutes";
import taskRoutes from "./routes/taskRoutes";
import userRoutes from "./routes/userRoutes";
import authRoutes from "./routes/authRoutes";
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

app.use("/auth", authRoutes);                 
app.use("/projects", projectRoutes);  
app.use("/users",userRoutes);      
app.use("/analysis", analysisRoutes);
app.use("/summary",summaryRoutes);
app.use("/task",taskRoutes);
app.use("/github", githubRoutes);
app.use(errorHandler);

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

const PORT = process.env.PORT || 4000;

app.listen(PORT, () => {
  console.log(`Node.js Backend server is running on port ${PORT}`);
});

console.log("current database url=", process.env.DATABASE_URL);