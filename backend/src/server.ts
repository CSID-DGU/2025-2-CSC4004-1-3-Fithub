import dotenv from "dotenv";
dotenv.config();

import express from "express";
import cors from "cors";
import helmet from "helmet";

// Route imports
import githubRoutes from "./routes/githubRoutes";
import projectRoutes from "./routes/projectRoutes";
import analysisRoutes from "./routes/analysisRoutes";
import recommendationRoutes from "./routes/recommendationRoutes";

import userRoutes from "./routes/userRoutes";
import authRoutes from "./routes/authRoutes";



// Middleware
import { errorHandler } from "./middleware/errorHandler";

// BigInt JSON 대응
(BigInt.prototype as any).toJSON = function () {
  return this.toString();
};

const app = express();

// CORS 설정
app.use(
  cors({
    origin: "*",
    credentials: true,
  })
);

// 보안 헤더
app.use(helmet());

// JSON 파싱
app.use(express.json());

// 라우터 등록
app.use("/auth", authRoutes);
app.use("/projects", projectRoutes);
app.use("/users", userRoutes);
app.use("/analysis", analysisRoutes);
app.use("/github", githubRoutes);
app.use("/recommendations", recommendationRoutes);


// 에러 핸들러
app.use(errorHandler);

// 헬스 체크
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// 서버 실행
const PORT = process.env.PORT || 4000;

app.listen(PORT, () => {
  console.log(`Node.js Backend server is running on port ${PORT}`);
});

console.log("current database url=", process.env.DATABASE_URL);
