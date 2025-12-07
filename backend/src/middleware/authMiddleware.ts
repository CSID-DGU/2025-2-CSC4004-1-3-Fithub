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
console.log("AUTH HEADER:", req.headers.authorization);
console.log("USING SECRET:", process.env.JWT_SECRET);

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Missing or invalid Authorization header",
    });
  }

  const token = authHeader.substring("Bearer ".length);
console.log("TOKEN:", token);

  try {
    const payload = verifyToken(token);
    req.user = { id: payload.userId };
    console.log("Verifying token:", token);

    next();
  } catch (err:any) {
    console.log("VERIFY ERROR:", err.message);
    return res.status(401).json({
      error: "Invalid or expired token",
    });
  }
};

