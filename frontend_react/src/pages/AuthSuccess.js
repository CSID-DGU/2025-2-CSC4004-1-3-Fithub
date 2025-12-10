// src/pages/AuthSuccess.js
import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AuthSuccess() {
  const [params] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const token = params.get("token");
    if (!token) return navigate("/login");

    // JWT Payload Decode
    const payload = JSON.parse(atob(token.split(".")[1]));

    // user 정보는 payload 내부에 userId 등 포함 → BE에서 user 객체를 추가로 줄 수도 있음
    const user = {
      id: payload.userId,
      login: payload.login,
      avatarUrl: payload.avatarUrl,
    };

    // AuthContext 저장
    login(user, token);

    // 메인 페이지로 이동
    navigate("/", { replace: true });
  }, []);

  return null;
}
