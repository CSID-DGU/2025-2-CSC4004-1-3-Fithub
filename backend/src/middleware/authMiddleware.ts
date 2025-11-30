import { Request, Response, NextFunction } from "express";
import { verifyToken } from "../jwt";

export interface AuthRequest extends Request {
  user?: { id: number };
}

declare module "express-serve-static-core" {
  interface Request {
    user?: {
      id: number;
      role?: string;
      github_id?: number;
      username?: string;
    };
  }
}
export const requireAuth = (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Missing or invalid Authorization header",
    });
  }

  const token = authHeader.substring("Bearer ".length);

  try {
    const payload = verifyToken(token);
    req.user = { id: payload.userId };
    next();
  } catch (err) {
    return res.status(401).json({
      error: "Invalid or expired token",
    });
  }
};
