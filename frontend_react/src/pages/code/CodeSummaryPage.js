import React, { useEffect, useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { runAnalysis } from "../../api/analysisApi"; // 혹시 모를 비상용

export default function CodeSummaryPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [summaryList, setSummaryList] = useState([]);
  const [repoSummary, setRepoSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [repoInfo, setRepoInfo] = useState(null);

  // 1. 데이터 불러오기 (State -> Storage -> API 순서)
  useEffect(() => {
    // 1) State로 넘겨준 데이터 확인 (ProjectDetail에서 옴)
    if (location.state && location.state.preloadedData) {
      console.log("📦 State로 전달된 요약 데이터를 사용합니다.");
      setRepoInfo(location.state.repo);
      setSummaryList(location.state.preloadedData.summary || []);
      setRepoSummary(location.state.preloadedData.repoSummary || "");
      setLoading(false);
      return;
    }

    // 2) State가 없으면 로컬 스토리지에서 Repo ID 찾기
    const savedRepoId = localStorage.getItem("selectedRepo");
    if (!savedRepoId) {
      alert("선택된 프로젝트가 없습니다.");
      navigate("/");
      return;
    }

    // 3) 세션 스토리지(캐시) 확인 (헤더 버튼 등)
    const cachedKey = `analysis_cache_${savedRepoId}`;
    const cachedData = sessionStorage.getItem(cachedKey);

    if (cachedData) {
      console.log("💾 저장된(캐시) 요약 데이터를 불러옵니다.");
      const parsed = JSON.parse(cachedData);
      
      // Repo 정보는 없으니 ID라도 세팅
      setRepoInfo({ repo_id: savedRepoId, name: "Current Repository" });
      
      // 데이터 파싱
      if (Array.isArray(parsed.summary)) {
        setSummaryList(parsed.summary);
      } else if (parsed.file_summaries) {
        setSummaryList(parsed.file_summaries);
      }
      
      if (typeof parsed.summary === "string") {
        setRepoSummary(parsed.summary);
      } else if (parsed.repo_summary) { // 백엔드 필드명에 따라 다름
        setRepoSummary(parsed.repo_summary);
      }
      
      setLoading(false);
      return;
    }

    // 4) [최후의 수단] 캐시도 없으면... 
    console.warn("⚠️ 표시할 데이터가 없습니다. (분석 미실행)");
    setLoading(false);

  }, [location.state, navigate]);

  // --- 렌더링 ---
  if (loading) return <div style={{padding: "50px", textAlign: "center"}}>로딩 중...</div>;

  return (
    <div style={{ padding: "20px", maxWidth: "1000px", margin: "0 auto" }}>
      <header style={{ display: "flex", alignItems: "center", marginBottom: "30px" }}>
        <button onClick={() => navigate(-1)} style={{ background: "none", border: "1px solid #ccc", borderRadius: "50%", width: "32px", height: "32px", cursor: "pointer", marginRight: "10px" }}>←</button>
        <h1 style={{ margin: 0 }}>🧠 {repoInfo?.name || "Code"} Summary</h1>
      </header>

      {summaryList.length === 0 && !repoSummary ? (
        <div style={{textAlign: "center", padding: "40px", background: "#f9f9f9", borderRadius: "10px"}}>
          <h3>데이터가 없습니다.</h3>
          <p>프로젝트 대시보드에서 <strong>[최신 상태 업데이트]</strong>를 먼저 진행해주세요.</p>
          <button onClick={() => navigate(-1)} style={{padding: "10px 20px", background: "#333", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", marginTop: "10px"}}>돌아가기</button>
        </div>
      ) : (
        <>
          {/* 전체 요약 섹션 */}
          {repoSummary && (
            <div style={{ marginBottom: "30px", padding: "20px", background: "#eef2ff", borderRadius: "12px", border: "1px solid #c7d2fe" }}>
              <h2 style={{ marginTop: 0, fontSize: "18px", color: "#3730a3" }}>📄 Repository Overview</h2>
              <p style={{ lineHeight: "1.6", color: "#333" }}>{repoSummary}</p>
            </div>
          )}

          {/* 파일별 요약 리스트 */}
          <div style={{ display: "grid", gap: "15px" }}>
            {summaryList.map((item, idx) => (
              <div key={idx} style={{ padding: "15px", background: "white", borderRadius: "10px", boxShadow: "0 2px 8px rgba(0,0,0,0.05)", border: "1px solid #eee" }}>
                <div style={{ fontWeight: "bold", fontSize: "16px", marginBottom: "5px", color: "#007bff" }}>
                  📄 {item.path || item.file_name}
                </div>
                <div style={{ color: "#555", lineHeight: "1.5", fontSize: "14px" }}>
                  {item.summary}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}