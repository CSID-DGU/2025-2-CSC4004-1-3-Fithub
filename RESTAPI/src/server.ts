import express from "express";
import cors from "cors";
import helmet from "helmet";
import githubRoutes from "./routes/githubRoutes";
import { errorHandler } from "./middleware/errorHandler";

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use("/api/github", githubRoutes);

app.use(errorHandler);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`GitHub backend is running on port ${PORT}`);
});
