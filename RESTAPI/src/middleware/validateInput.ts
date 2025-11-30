import { Request, Response, NextFunction } from "express";

export function requireGitHubToken(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.header("Authorization");
  const token =
    authHeader?.startsWith("Bearer ")
      ? authHeader.slice("Bearer ".length).trim()
      : (req.body.token as string | undefined);

  if (!token) {
    return res.status(400).json({
      error: "GITHUB_TOKEN_MISSING",
      message: "Authorization: Bearer <token> 또는 body.token을 제공해야 합니다."
    });
  }

  (req as any).githubToken = token;
  next();
}

export function requireRepoFullName(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const { repoFullName, branch } = req.body as {
    repoFullName?: string;
    branch?: string;
  };

  if (!repoFullName || typeof repoFullName !== "string") {
    return res.status(400).json({
      error: "REPO_FULL_NAME_MISSING",
      message: 'body.repoFullName은 "owner/repo" 형태의 문자열이어야 합니다.'
    });
  }

  const parts = repoFullName.split("/");
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    return res.status(400).json({
      error: "REPO_FULL_NAME_INVALID",
      message: 'repoFullName은 반드시 "owner/repo" 형식이어야 합니다.'
    });
  }

  (req as any).owner = parts[0];
  (req as any).repo = parts[1];
  (req as any).branch = typeof branch === "string" ? branch : undefined;

  next();
}
