import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import { 
  getProjectList, 
  deleteProject 
} from "../api/projectApi";

export default function MainDashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);

  // DB에서 프로젝트 목록 불러오기
  useEffect(() => {
    if (!token) return;

    localStorage.removeItem("selectedRepo");
    localStorage.removeItem("selectedRepoName");
    localStorage.removeItem("currentProjectId");
    
    async function load() {
      try {
        const list = await getProjectList(token);
        setProjects(list);
      } catch (err) {
        console.error(err);
        alert("프로젝트 목록을 불러오지 못했습니다.");
      }
    }
    load();
  }, [token]);

  async function handleDelete(projectId) {
    if (!window.confirm("정말 삭제하시겠습니까?")) return;

    try {
      await deleteProject(projectId, token);
      setProjects(projects.filter((p) => p.id !== projectId));
    } catch (err) {
      console.error(err);
      alert("삭제 실패: " + err.message);
    }
  }

  return (
    <div className="dashboard-container">
      <h2>내 프로젝트</h2>

      <button 
        className="create-new-btn" 
        onClick={() => navigate("/projects/create")}
      >
        새 프로젝트 만들기 ➕
      </button>

      <div className="project-list">
        {projects.length === 0 && <p>아직 생성된 프로젝트가 없습니다.</p>}

        {projects.map((p) => (
          <div key={p.id} className="project-card">
            <h3>{p.name}</h3>
            <p>프로젝트 ID: {p.id}</p>

            <div className="btn-group">
              <button onClick={() => navigate(`/projects/${p.id}`)}>
                상세 보기
              </button>

              <button onClick={() => handleDelete(p.id)}>
                삭제하기
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
