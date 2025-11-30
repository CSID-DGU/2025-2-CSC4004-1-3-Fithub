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
import swaggerUi from "swagger-ui-express";
import YAML from "yamljs";
import dotenv from "dotenv";
dotenv.config();

(BigInt.prototype as any).toJSON = function () {
  return this.toString();
};

const app = express();
const swaggerDocument = YAML.load("./src/openapi.yaml");

app.use(cors());
app.use(helmet());
app.use(express.json());
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

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
app.use("/api/github", githubRoutes);
app.use("/graph",graphRoutes);
app.use(errorHandler);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Node.js Backend server is running on port ${PORT}`);
});

console.log("current database url=", process.env.DATABASE_URL);
