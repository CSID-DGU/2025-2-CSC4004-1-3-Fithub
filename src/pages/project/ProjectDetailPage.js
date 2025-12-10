import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getProject, addRepoToProject } from "../../api/projectApi";
import { useAuth } from "../../context/AuthContext";

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const { token } = useAuth();

  const [project, setProject] = useState(null);
  const [repoUrl, setRepoUrl] = useState("");

  useEffect(() => {
    if (!token) return;
    load();
  }, [token]);

  const load = async () => {
    try {
      const data = await getProject(projectId, token);
      setProject(data);
    } catch (err) {
      console.error(err);
      alert("프로젝트 정보를 불러오지 못했습니다.");
    }
  };

  const handleAddRepo = async () => {
    if (!repoUrl.trim()) return alert("레포 URL 입력!");

    try {
      await addRepoToProject(projectId, { repoUrl }, token);
      alert("레포가 등록되었습니다!");
      load();
    } catch (err) {
      console.error(err);
      alert("레포 추가 실패");
    }
  };

  return (
    <div className="container">
      {project ? (
        <>
          <h2>프로젝트: {project.name}</h2>

          <div className="card">
            <input
              placeholder="GitHub Repo URL"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
            <button onClick={handleAddRepo}>레포 연결</button>
          </div>

          <h3>등록된 Repositories</h3>
          <ul>
            {project.repos?.map((r) => (
              <li key={r.repoId}>{r.url}</li>
            ))}
          </ul>
        </>
      ) : (
        "Loading..."
      )}
    </div>
  );
}
