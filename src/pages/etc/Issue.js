import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getIssues, getIssueDetail } from "../../api/githubApi";

export default function Issue() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const repoId = localStorage.getItem("selectedRepo");

  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);

  // 상세 정보 관리 (캐싱)
  const [openIssueId, setOpenIssueId] = useState(null); // UI 토글용 (고유 ID)
  const [issueDetails, setIssueDetails] = useState({}); // 데이터 저장용 (Key: issueNumber)
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!repoId || repoId === "undefined" || repoId === "null") {
      alert("⚠️ 먼저 프로젝트(Repository)를 선택해주세요.");
      navigate("/projects");
      return;
    }
    loadIssues();
  }, [repoId, token, navigate]);

  const loadIssues = async () => {
    setLoading(true);
    try {
      const data = await getIssues(repoId, token);
      if (Array.isArray(data)) {
        // URL 필터링: issues가 포함된 것만
        const realIssues = data.filter((item) => 
          item.issueUrl && item.issueUrl.includes("/issues/")
        );
        setIssues(realIssues);
      } else {
        setIssues([]);
      }
    } catch (err) {
      console.error(err);
      setIssues([]);
    }
    setLoading(false);
  };

  // 상세 조회 요청 함수
  const toggleDetail = async (issueNum, issueId) => {
    console.log(`🖱️ 클릭! Number: ${issueNum}, ID: ${issueId}`);

    // 1. 닫기
    if (openIssueId === issueId) {
      setOpenIssueId(null);
      return;
    }

    // 2. 열기
    setOpenIssueId(issueId);

    // 3. 캐싱 확인 (이미 불러온 적 있으면 API 요청 안 함)
    if (issueDetails[issueNum]) {
        console.log("📦 캐시된 데이터 사용");
        return;
    }

    // 4. API 요청
    setDetailLoading(true);
    try {
      // 여기서 issueNum(176)을 넘김
      const detail = await getIssueDetail(repoId, issueId, token);
      console.log("✅ 상세 조회 성공:", detail);
      
      setIssueDetails(prev => ({ ...prev, [issueId]: detail }));
    } catch (err) {
      console.error("❌ 상세 조회 에러:", err);
      // 에러 나면 닫아버리거나, 사용자에게 알림
    }
    setDetailLoading(false);
  };

  const getStatusBadge = (state) => {
    if (state === "open") return <Badge bg="#28a745" text="🟢 Open" />;
    return <Badge bg="#d73a49" text="🔴 Closed" />;
  };

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "bold" }}>🐞 Issues</h2>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden", border: "1px solid #e1e4e8", borderRadius: "6px" }}>
        {loading ? (
          <p style={{ padding: "30px", textAlign: "center" }}>로딩 중...</p>
        ) : issues.length === 0 ? (
          <div style={{ padding: "50px", textAlign: "center", color: "#999" }}>
            <p>등록된 이슈가 없습니다.</p>
          </div>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {issues.map((item) => {
              const issueId = item.issueId;       // 리액트 Key용
              const issueNum = item.issueNumber;  // API 요청용 (#176)
              const isOpen = openIssueId === issueId;
              
              // 상세 데이터: API 데이터 우선, 없으면 목록 데이터 사용
              const detailData = issueDetails[issueNum] || item; 

              return (
                <li key={issueId} style={{ borderBottom: "1px solid #eee" }}>
                  
                  {/* 헤더 (클릭 시 토글) */}
                  <div 
                    // 여기서 번호(issueNum)와 ID(issueId)를 둘 다 넘겨야 함
                    onClick={() => toggleDetail(issueNum, issueId)}
                    style={{ 
                      padding: "20px 24px", 
                      cursor: "pointer", 
                      display: "flex", 
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      backgroundColor: isOpen ? "#f8f9fa" : "white",
                      transition: "0.2s"
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", width: "100%" }}>
                      <div style={{ display: "flex", alignItems: "flex-start", marginBottom: "4px" }}>
                        <div style={{ flexShrink: 0, marginTop: "2px", marginRight: "10px" }}>
                          {getStatusBadge(item.state || "open")}
                        </div>
                        <div style={{ fontWeight: "600", fontSize: "16px", lineHeight: "1.4", wordBreak: "break-word" }}>
                          {item.title}
                        </div>
                      </div>
                      <div style={{ fontSize: "12px", color: "#666", marginLeft: "2px" }}>
                        #{issueNum} • opened by <strong>{item.author?.login || "Unknown"}</strong>
                      </div>
                    </div>
                    
                    <div style={{ color: "#aaa", fontSize: "12px", marginTop: "6px", marginLeft: "15px", flexShrink: 0 }}>
                       {isOpen ? "접기 ▲" : "더보기 ▼"}
                    </div>
                  </div>

                  {/* 상세 내용 영역 */}
                  {isOpen && (
                    <div style={{ padding: "20px 30px", backgroundColor: "#fafbfc", borderTop: "1px solid #eee" }}>
                      
                      {/* 로딩 표시 */}
                      {detailLoading && !issueDetails[issueNum] ? (
                        <p style={{ color: "#666", textAlign: "center", margin: "20px 0" }}>
                          상세 정보를 불러오는 중입니다...
                        </p>
                      ) : (
                        <>
                          <div style={{ 
                            whiteSpace: "pre-wrap", 
                            color: "#333", 
                            fontSize: "14px", 
                            lineHeight: "1.6", 
                            marginBottom: "20px",
                            overflowX: "auto"
                          }}>
                            {detailData.body ? detailData.body : <span style={{color: "#999"}}>{`내용이 없습니다. (작성일: ${new Date(detailData.createdAt).toLocaleDateString()})`}
                              </span>}
                          </div>
                          
                          <div style={{ textAlign: "right" }}>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(item.issueUrl, "_blank");
                              }}
                              style={{ padding: "6px 12px", fontSize: "12px", backgroundColor: "#24292e", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
                            >
                              GitHub에서 보기 ↗
                            </button>
                          </div>
                        </>
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

function Badge({ bg, text }) {
  return (
    <span style={{ backgroundColor: bg, color: "white", padding: "4px 10px", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", display: "inline-block", whiteSpace: "nowrap" }}>
      {text}
    </span>
  );
}