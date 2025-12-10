import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function RepoListPage() {
  const [repos, setRepos] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("userRepos") || "[]");
    setRepos(stored);
  }, []);

  const handleSelectRepo = (repo) => {
    navigate(`/dashboard?repo=${encodeURIComponent(repo)}`);
  };

  return (
    <div className="dashboard-content">
      <h2 style={{ marginBottom: "20px" }}>My Repositories</h2>

      {repos.length === 0 ? (
        <div className="dashboard-locked" style={{ width: "60%" }}>
          <p>등록된 레포지토리가 없습니다.</p>
          <button
            className="signout-btn"
            onClick={() => navigate("/mypage")}
          >
            레포 등록하러 가기 →
          </button>
        </div>
      ) : (
        <div className="card" style={{ maxWidth: "600px" }}>
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {repos.map((repo, idx) => (
              <li
                key={idx}
                style={{
                  padding: "14px 10px",
                  borderBottom: "1px solid #ddd",
                  cursor: "pointer"
                }}
                onClick={() => handleSelectRepo(repo)}
              >
                {repo}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="signout-btn"
        style={{ marginTop: "20px" }}
        onClick={() => navigate("/mypage")}
      >
        레포 추가하기
      </button>
    </div>
  );
}
