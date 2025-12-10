// src/pages/ProjectCreate.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import { createProject, addRepoToProject, startSnapshot, addProjectMember } from "../api/projectApi";

export default function ProjectCreate() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const [projectName, setProjectName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    if (!projectName.trim()) return alert("프로젝트 이름을 입력하세요.");
    if (!repoUrl.trim()) return alert("Repository URL을 입력하세요.");
    if (!token) return alert("로그인이 필요합니다.");

    setLoading(true);

    try {
      // 1) 프로젝트 생성
      const project = await createProject(
        { name: projectName, description: "" },
        token
      );

      // 프로젝트 생성자의 userId를 members에 자동 등록
      await addProjectMember(project.id, project.ownerId, token);

      // 2) Repo URL 파싱
      const cleaned = repoUrl
        .replace("https://github.com/", "")
        .replace("http://github.com/", "")
        .replace(".git", "")
        .trim();

      const [owner, repo] = cleaned.split("/");

      if (!owner || !repo) {
        alert("올바른 GitHub Repo URL이 아닙니다.");
        setLoading(false);
        return;
      }

      // 3) Repo 연결
      await addRepoToProject(project.id, owner, repo, token);

      // 4) 자동 분석 시작 (Repo Snapshot 생성)
      await startSnapshot(`${owner}/${repo}`, token);

      alert("프로젝트 생성 및 분석이 시작되었습니다!");

      // 5) → 목록으로 이동
      navigate("/projects");

    } catch (err) {
      console.error(err);
      alert("프로젝트 생성 중 오류 발생: " + err.message);
    }

    setLoading(false);
  }

  return (
    <div className="project-create-container">
      <div className="project-create-card">

        <h2>새 프로젝트 생성</h2>

        <label className="label">프로젝트 이름</label>
        <input
          className="input"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="My New Project"
        />

        <label className="label">GitHub Repository URL</label>
        <input
          className="input"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/user/repo"
        />

        <button 
          className="create-btn" 
          onClick={handleCreate}
          disabled={loading}
        >
          {loading ? "생성 + 분석 중..." : "프로젝트 생성하기"}
        </button>
      </div>
    </div>
  );
}
