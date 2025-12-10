import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getCommits } from "../../api/githubApi";
import { useNavigate } from "react-router-dom";

export default function CodeOwnersPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const repoId = localStorage.getItem("selectedRepo");

  const [owners, setOwners] = useState([]);
  const [totalCommits, setTotalCommits] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !repoId) {
      alert("프로젝트와 레포지토리를 먼저 선택해주세요.");
      navigate("/projects");
      return;
    }
    analyzeCommits();
  }, [token, repoId]);

  const analyzeCommits = async () => {
    try {
      // 1. 커밋 리스트 가져오기
      const commitList = await getCommits(repoId, token);
      setTotalCommits(commitList.length);

      // 2. 작성자별 커밋 수 계산 (Reduce)
      const stats = commitList.reduce((acc, commit) => {
        const author = commit.author_name || "Unknown";
        acc[author] = (acc[author] || 0) + 1;
        return acc;
      }, {});

      // 3. 배열로 변환 및 정렬 (커밋 수 내림차순)
      const sortedOwners = Object.entries(stats)
        .map(([name, count]) => ({
          name,
          count,
          percentage: ((count / commitList.length) * 100).toFixed(1),
        }))
        .sort((a, b) => b.count - a.count);

      setOwners(sortedOwners);
    } catch (err) {
      console.error(err);
      // alert("데이터 분석 중 오류가 발생했습니다.");
    }
    setLoading(false);
  };

  if (loading) return <div style={{ padding: 40 }}>데이터 분석 중... 📊</div>;

  return (
    <div className="dashboard-container">
      <h2>🏆 Code Owners & Contributors</h2>
      <p style={{ color: "#666", marginBottom: "20px" }}>
        커밋 기록을 분석하여 프로젝트 기여도를 보여줍니다. (Total Commits: {totalCommits})
      </p>

      <div className="card" style={{ padding: "30px" }}>
        {owners.length === 0 ? (
          <p>커밋 기록이 없습니다.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {owners.map((owner, index) => (
              <div key={owner.name}>
                {/* 이름과 수치 */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "6px",
                    fontWeight: index < 3 ? "bold" : "normal", // Top 3는 굵게
                    color: index === 0 ? "#d35400" : "#333", // 1등은 색상 강조
                  }}
                >
                  <span>
                    {index + 1}. {owner.name} {index === 0 && "👑"}
                  </span>
                  <span>
                    {owner.count} commits ({owner.percentage}%)
                  </span>
                </div>

                {/* 그래프 바 (CSS로 구현) */}
                <div
                  style={{
                    width: "100%",
                    height: "10px",
                    background: "#eee",
                    borderRadius: "5px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${owner.percentage}%`,
                      height: "100%",
                      background: index === 0 ? "#f2994a" : "#4a90e2", // 1등은 주황, 나머진 파랑
                      transition: "width 1s ease-in-out",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}