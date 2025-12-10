import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getPulls, getPullDetail } from "../api/githubApi";

export default function PullRequest() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const repoId = localStorage.getItem("selectedRepo");

  const [pulls, setPulls] = useState([]);
  const [filter, setFilter] = useState("all"); // 'all' | 'open' | 'closed' | 'merged'
  const [loading, setLoading] = useState(true);
  
  // 상세 정보 토글용 상태
  const [openPrId, setOpenPrId] = useState(null);
  const [prDetail, setPrDetail] = useState({});
  const [detailLoading, setDetailLoading] = useState(false);

  // Guard: 프로젝트 선택 확인
  useEffect(() => {
    if (!repoId || repoId === "undefined" || repoId === "null") {
      alert("⚠️ 먼저 프로젝트(Repository)를 선택해주세요.");
      navigate("/projects");
      return;
    }
    loadPulls();
  }, [repoId, token, navigate]);

  const loadPulls = async () => {
    setLoading(true);
    try {
      const data = await getPulls(repoId, token);
      
      if (Array.isArray(data)) {
        // 백엔드에서 type을 준다면 필터링 (안 준다면 그냥 data 전체 사용)
        const onlyPRs = data.filter((item) => item.type === 'pr');
        setPulls(onlyPRs.length > 0 ? onlyPRs : data);
      } else {
        setPulls([]);
      }
    } catch (err) {
      console.error(err);
      setPulls([]);
    }
    setLoading(false);
  };

  // 상세 정보 가져오기 (토글)
  const toggleDetail = async (number) => {
    console.log("🖱️ [PR Click] 전달받은 번호:", number);

    if (!number) {
      console.error("❌ Error: PR 번호(ID)가 없습니다.");
      return;
    }

    if (openPrId === number) {
      setOpenPrId(null);
      return;
    }
    setOpenPrId(number);

    // 캐싱 확인
    if (prDetail[number]) return;

    setDetailLoading(true);
    try {
      const detail = await getPullDetail(repoId, number, token);
      console.log("✅ PR 상세 데이터:", detail);
      setPrDetail(prev => ({ ...prev, [number]: detail }));
    } catch (err) {
      console.error("PR 상세 조회 실패:", err);
    }
    setDetailLoading(false);
  };

  // 필터링 로직
  const filteredPulls = pulls.filter((pr) => {
    if (filter === "all") return true;
    if (filter === "open") return pr.state === "open";
    if (filter === "merged") return pr.merged_at !== null;
    if (filter === "closed") return pr.state === "closed" && pr.merged_at === null;
    return true;
  });

  // 상태 뱃지 UI
  const getStatusBadge = (pr) => {
    if (pr.state === "open") {
      return <Badge bg="#28a745" text="🟢 Open" />;
    } else if (pr.merged_at) {
      return <Badge bg="#6f42c1" text="🟣 Merged" />;
    } else {
      return <Badge bg="#d73a49" text="🔴 Closed" />;
    }
  };

  return (
    <div className="dashboard-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <h2 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "5px" }}>🔀 Pull Requests</h2>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <FilterBtn current={filter} type="all" setFilter={setFilter} label={`All (${pulls.length})`} />
          <FilterBtn current={filter} type="open" setFilter={setFilter} label="Open" />
          <FilterBtn current={filter} type="merged" setFilter={setFilter} label="Merged" />
          <FilterBtn current={filter} type="closed" setFilter={setFilter} label="Closed" />
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <p style={{ padding: "30px", textAlign: "center" }}>PR 목록을 불러오는 중...</p>
        ) : filteredPulls.length === 0 ? (
          <div style={{ padding: "50px", textAlign: "center", color: "#999" }}>
            <p style={{ fontSize: "18px" }}>해당 상태의 Pull Request가 없습니다.</p>
          </div>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {filteredPulls.map((pr) => {
              
              // pull_id가 있으면 그걸 쓰고, 없으면 number, id 순으로 찾습니다.
              const realPrNum = pr.pull_id || pr.number || pr.id;

              const isOpen = openPrId === realPrNum;
              const authorImg = pr.author?.avatar_url || "https://github.com/identicons/jason.png";
              const authorName = pr.author?.login || "Unknown";

              // 변수 선언 후 여기서 return 시작
              return (
                <li key={realPrNum} style={{ borderBottom: "1px solid #eee" }}>
                  
                  {/* 1. PR 카드 헤더 */}
                  <div 
                    onClick={() => toggleDetail(realPrNum)} // 위에서 찾은 ID 사용
                    style={{ 
                      padding: "20px 24px", 
                      cursor: "pointer", 
                      display: "flex", 
                      justifyContent: "space-between",
                      alignItems: "center",
                      backgroundColor: isOpen ? "#f8f9fa" : "white",
                      transition: "0.2s"
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                        {getStatusBadge(pr)}
                        <span style={{ fontSize: "16px", fontWeight: "600", color: "#333" }}>{pr.title}</span>
                      </div>
                      <div style={{ fontSize: "13px", color: "#666", paddingLeft: "4px" }}>
                        #{realPrNum} • opened by <strong>{authorName}</strong> 
                        {' '} • {new Date(pr.created_at).toLocaleDateString()}
                        {' '} <span style={{ color: "#aaa" }}>|</span> 
                        <code style={{ background: "#eee", padding: "2px 5px", borderRadius: "4px", margin: "0 5px", color: "#333" }}>{pr.base?.ref}</code> 
                        ← 
                        <code style={{ background: "#e1f5fe", padding: "2px 5px", borderRadius: "4px", marginLeft: "5px", color: "#0277bd" }}>{pr.head?.ref}</code>
                      </div>
                    </div>
                    <div style={{ color: "#aaa", fontSize: "12px" }}>
                      {isOpen ? "접기 ▲" : "더보기 ▼"}
                    </div>
                  </div>

                  {/* 2. 상세 정보 패널 */}
                  {isOpen && (
                    <div style={{ padding: "20px 30px", background: "#fafbfc", borderTop: "1px solid #eee" }}>
                      {detailLoading && !prDetail[realPrNum] ? (
                        <p>상세 정보 로딩 중...</p>
                      ) : (
                        <div>
                          <div style={{ display: "flex", gap: "20px", marginBottom: "15px", fontSize: "14px" }}>
                            <span style={{ color: "#28a745" }}>➕ {prDetail[realPrNum]?.additions || 0} additions</span>
                            <span style={{ color: "#d73a49" }}>➖ {prDetail[realPrNum]?.deletions || 0} deletions</span>
                            <span style={{ color: "#586069" }}>📄 {prDetail[realPrNum]?.changed_files || 0} files changed</span>
                          </div>

                          <div style={{ background: "white", padding: "15px", borderRadius: "8px", border: "1px solid #ddd", fontSize: "14px", lineHeight: "1.6", color: "#24292e" }}>
                            {prDetail[realPrNum]?.body ? prDetail[realPrNum].body : <span style={{ color: "#999" }}>(설명 없음)</span>}
                          </div>

                          <div style={{ marginTop: "15px", textAlign: "right" }}>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(pr.html_url, "_blank");
                              }}
                              style={{ padding: "8px 16px", background: "#24292e", color: "white", border: "none", borderRadius: "6px", cursor: "pointer" }}
                            >
                              GitHub에서 보기 ↗
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

// --- 보조 컴포넌트들 ---
function Badge({ bg, text }) {
  return (
    <span style={{
      backgroundColor: bg, color: "white", padding: "4px 10px", 
      borderRadius: "20px", fontSize: "12px", fontWeight: "bold"
    }}>
      {text}
    </span>
  );
}

function FilterBtn({ current, type, setFilter, label }) {
  const isActive = current === type;
  return (
    <button
      onClick={() => setFilter(type)}
      style={{
        padding: "8px 14px",
        borderRadius: "20px",
        border: isActive ? "1px solid #333" : "1px solid #ddd",
        background: isActive ? "#333" : "white",
        color: isActive ? "white" : "#555",
        cursor: "pointer",
        fontSize: "13px",
        fontWeight: isActive ? "600" : "400",
        transition: "0.2s"
      }}
    >
      {label}
    </button>
  );
}