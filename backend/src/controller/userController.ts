import { Request, Response } from "express";
import prisma from "../prisma";
import { AuthRequest } from "../middleware/authMiddleware";
import { Prisma } from "@prisma/client";

export const getMyGitHubProfile = async (req: AuthRequest, res: Response) => {
  try {
    // 인증 정보 미존재
    if (!req.user || !req.user.id) {
      return res.status(401).json({ error: "Unauthorized: user not found in token" });
    }

    const userId = req.user.id;

    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      return res.status(404).json({ error: "User not found in database" });
    }

    return res.json({
      id: user.id,
      githubId: user.githubId,
      login: user.login,
      avatarUrl: user.avatarUrl,
      name: user.name,
      email: user.email,
      createdAt: user.createdAt,
    });

  } catch (err: any) {
    console.error("Get GitHub profile error:", err);

    // 📌 Prisma Known Request Error
    if (err instanceof Prisma.PrismaClientKnownRequestError) {
      return res.status(400).json({
        error: "Database error",
        code: err.code,
        message: err.message,
      });
    }

    // 📌 Prisma Validation Error
    if (err instanceof Prisma.PrismaClientValidationError) {
      return res.status(400).json({
        error: "Database validation error",
        message: err.message,
      });
    }

    // 📌 Prisma Unknown Error
    if (err instanceof Prisma.PrismaClientUnknownRequestError) {
      return res.status(500).json({
        error: "Unknown database error",
        message: err.message,
      });
    }

    // 📌 기본 Fallback
    return res.status(500).json({
      error: "Internal server error while fetching profile",
      message: err.message || "Unknown server error",
    });
  }
};
