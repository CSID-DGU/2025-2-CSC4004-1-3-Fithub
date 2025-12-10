import React, { useEffect, useState } from "react";
import { getMyProjects, createProject } from "../../api/projectApi";
import { useAuth } from "../../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function ProjectListPage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [projectName, setProjectName] = useState("");

  useEffect(() => {
    if (!token) return;
    load();
  }, [token]);

  const load = async () => {
    try {
      const data = await getMyProjects(token);
      setProjects(data);
    } catch (err) {
      console.error(err);
      alert("프로젝트 목록을 불러오지 못했습니다.");
    }
  };

  const handleCreate = async () => {
    if (!projectName.trim()) return alert("프로젝트 이름을 입력해주세요!");

    try {
      const data = await createProject({ name: projectName }, token);
      alert("프로젝트가 생성되었습니다!");
      navigate(`/projects/${data.projectId}`);
    } catch (err) {
      console.error(err);
      alert("프로젝트 생성 실패");
    }
  };

  return (
    <div className="container">
      <h2>내 프로젝트</h2>

      <div className="card">
        <input
          placeholder="프로젝트 이름 입력"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
        />
        <button onClick={handleCreate}>프로젝트 생성</button>
      </div>

      <h3>Project List</h3>
      <ul>
        {projects.map((p) => (
          <li
            key={p.projectId}
            style={{ cursor: "pointer" }}
            onClick={() => navigate(`/projects/${p.projectId}`)}
          >
            {p.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
