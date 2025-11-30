import { Request, Response, NextFunction } from "express";

export function errorHandler(
  err: any,
  _req: Request,
  res: Response,
  _next: NextFunction
) {
  console.error("[ERROR]", err?.status || 500, err?.message);

  const status = err.status ?? 500;

  const payload: any = {
    error: "INTERNAL_ERROR",
    message: err?.message || "Internal server error"
  };

  if (err.response?.data) {
    payload.github = {
      status: err.response.status,
      data: err.response.data
    };
  }

  const rateLimitHeaders = err.response?.headers;
  if (rateLimitHeaders) {
    const rl = {
      limit: rateLimitHeaders["x-ratelimit-limit"],
      remaining: rateLimitHeaders["x-ratelimit-remaining"],
      reset: rateLimitHeaders["x-ratelimit-reset"]
    };
    payload.rateLimit = rl;
  }

  res.status(status).json(payload);
}
