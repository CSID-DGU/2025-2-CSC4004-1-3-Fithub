import React, { useState, useEffect, useMemo } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom"; 
import CodeGraph from "../../components/CodeGraph";
import TreeGraph from "../../components/TreeGraph";
import { buildTree, flattenTreeToGraph } from "../../utils/dataTransformer";

export default function CodeGraphPage() {
  const navigate = useNavigate();
  const location = useLocation(); 
  const { repoId } = useParams(); 

  // 상태 관리
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [rawData, setRawData] = useState(null);
  const [loading, setLoading] = useState(true);

  // 1. 레포 정보 식별 (ID 찾기용)
  const repoInfo = useMemo(() => {
    // 1) state로 넘어온 경우
    if (location.state && location.state.repo) return location.state.repo;
    // 2) URL에 ID가 있는 경우
    if (repoId && repoId !== "undefined") return { repo_id: repoId, name: `Repo-${repoId}` };
    // 3) 헤더 버튼 클릭 시: 마지막 저장된 ID 사용
    const savedRepoId = localStorage.getItem("selectedRepo");
    if (savedRepoId) return { repo_id: savedRepoId, name: "Current Repository" };
    return null;
  }, [location.state, repoId]);


  // 2. 데이터 로드 (API 호출 없이 오직 전달/저장된 데이터만 사용)
  useEffect(() => {
    if (!repoInfo) {
      alert("분석할 리포지토리 정보가 없습니다. 프로젝트 상세 페이지에서 먼저 분석을 진행해주세요.");
      navigate("/"); 
      return;
    }

    const loadData = () => {
      setLoading(true);

      // ProjectDetail에서 직접 들고 온 데이터 (전체보기 버튼)
      if (location.state && location.state.preloadedData) {
        console.log("📦 State로 전달된 데이터를 사용합니다.");
        setRawData({
            graph: location.state.preloadedData.graph,
            summary: location.state.preloadedData.summary
        });
        setLoading(false);
        return; 
      }

      // 헤더 버튼 클릭 시 세션 스토리지(캐시) 확인!
      const cachedKey = `analysis_cache_${repoInfo.repo_id}`;
      const cachedData = sessionStorage.getItem(cachedKey);
      
      if (cachedData) {
        console.log("💾 저장된(캐시) 분석 데이터를 불러옵니다.");
        const parsed = JSON.parse(cachedData);
        setRawData(parsed); 
        setLoading(false);
        return;
      }

      // 데이터가 아예 없으면 분석 거부
      console.warn("⚠️ 표시할 데이터가 없습니다. (이 페이지에서는 분석을 수행하지 않습니다)");
      alert("분석된 데이터가 없습니다.\n프로젝트 대시보드에서 [최신 상태 업데이트]를 먼저 진행해주세요.");
      navigate(`/project/${localStorage.getItem("currentProjectId") || ""}`); // 대시보드로 강제 이동
    };

    loadData();
  }, [repoInfo, navigate, location.state]);


  // 3. 데이터 변환 (Tree & Graph 생성)
  const processedData = useMemo(() => {
    if (!rawData || !rawData.graph || !rawData.graph.nodes) {
        return { flat: null, nested: null };
    }
    const nestedTree = buildTree(rawData.graph.nodes); 
    const flatGraphData = flattenTreeToGraph(nestedTree, rawData.graph.edges);

    return { flat: { graph: flatGraphData }, nested: nestedTree };
  }, [rawData]);


  // 4. 검색 핸들러
  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    const nodes = processedData.flat?.graph?.nodes || [];
    const found = nodes.find(n => (n.label && n.label.toLowerCase().includes(searchTerm.toLowerCase())));
    if (found) { setSelectedNode(found); setSearchTerm(""); } 
    else { alert("❌ 해당 노드를 찾을 수 없습니다."); }
  };


  if (loading) return <div style={styles.loadingContainer}><div style={styles.spinner} /><h3 style={{color: "#555"}}>🤖 데이터 로딩 중...</h3></div>;
  if (!processedData.flat) return null; // 데이터 없으면 위에서 navigate 되므로 빈 화면

  return (
    <div style={styles.pageContainer}>
      <header style={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button onClick={() => navigate(-1)} style={styles.backButtonSmall}>←</button>
            <h1 style={styles.title}>🧪 {repoInfo?.name} <span style={{fontSize: "14px", color: "#888", fontWeight: "normal", marginLeft: "10px"}}>Analysis Result</span></h1>
        </div>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px" }}>
          <input type="text" placeholder="파일명 검색" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} style={styles.searchInput} />
          <button type="submit" style={styles.searchButton}>Search</button>
        </form>
      </header>
      
      <div style={styles.contentWrapper}>
        <div style={styles.graphSection}>
          <div style={styles.graphCard}>
            <CodeGraph data={processedData.flat} onNodeClick={setSelectedNode} focusNode={selectedNode} />
             <div style={styles.cardLabel}>🕸️ Network View</div>
          </div>
          <div style={styles.graphCard}>
            <TreeGraph data={processedData.nested} onNodeClick={setSelectedNode} />
            <div style={styles.cardLabel}>🌳 Hierarchy View</div>
          </div>
        </div>

        {selectedNode && (
          <div style={styles.detailPanel}>
            <div style={styles.detailHeader}>
              <span style={{ background: selectedNode.color || (selectedNode.type === 'directory' ? '#3498db' : '#2ecc71'), ...styles.colorDot }}/>
              <span style={styles.typeLabel}>{selectedNode.type || "UNKNOWN"}</span>
            </div>
            <h2 style={styles.nodeTitle}>{selectedNode.label}</h2>
            <div style={styles.badgeContainer}>
              {selectedNode.importance && <Badge color="bg-blue-100 text-blue-800" label={`Imp: ${selectedNode.importance}`} />}
              <Badge color="bg-green-100 text-green-800" label={selectedNode.domain || "Common"} />
            </div>
            <hr style={styles.divider} />
            <h3 style={styles.sectionTitle}>🧠 AI Summary</h3>
            <div style={styles.summaryBox}>{selectedNode.summary || "요약 정보가 없습니다."}</div>
            
            {rawData.summary && !selectedNode.summary && (
               <div style={styles.repoSummaryBox}><h4>📄 Repository Summary</h4><p>{rawData.summary}</p></div>
            )}
            <button onClick={() => setSelectedNode(null)} style={styles.closeButton}>닫기</button>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
    loadingContainer: { height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", flexDirection: "column", gap: "20px" },
    spinner: { width: "50px", height: "50px", border: "5px solid #ccc", borderTop: "5px solid #333", borderRadius: "50%", animation: "spin 1s linear infinite" },
    errorContainer: { padding: "50px", textAlign: "center" },
    pageContainer: { width: "100%", height: "100vh", padding: "20px", boxSizing: "border-box", background: "#f0f0f0", display: "flex", flexDirection: "column" },
    header: { width: "100%", height: "60px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 },
    backButtonSmall: { background: "transparent", border: "1px solid #ccc", borderRadius: "50%", width: "32px", height: "32px", cursor: "pointer", fontSize: "16px" },
    title: { margin: 0, fontSize: "24px", color: "#333", display: "flex", alignItems: "baseline", gap: "10px" },
    searchInput: { padding: "10px 16px", borderRadius: "20px", border: "1px solid #ccc", width: "220px", outline: "none" },
    searchButton: { background: "#333", color: "white", border: "none", padding: "10px 20px", borderRadius: "20px", cursor: "pointer", fontWeight: "bold" },
    contentWrapper: { display: "flex", width: "100%", flex: 1, gap: "20px", overflow: "hidden" },
    graphSection: { flex: 1, display: "flex", flexDirection: "column", gap: "20px", minWidth: 0 },
    graphCard: { flex: 1, background: "#1a1a1a", borderRadius: "16px", overflow: "hidden", boxShadow: "0 4px 20px rgba(0,0,0,0.15)", position: "relative" },
    cardLabel: { position: "absolute", top: 15, left: 20, color: "white", fontWeight: "bold", zIndex: 10, pointerEvents: "none", textShadow: "0 2px 4px rgba(0,0,0,0.5)" },
    detailPanel: { width: "400px", flexShrink: 0, height: "100%", background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)", overflowY: "auto", boxSizing: "border-box" },
    detailHeader: { display: "flex", alignItems: "center", marginBottom: "12px" },
    colorDot: { width: "12px", height: "12px", borderRadius: "50%", marginRight: "8px" },
    typeLabel: { fontSize: "12px", fontWeight: "bold", color: "#888", textTransform: "uppercase" },
    nodeTitle: { fontSize: "20px", marginBottom: "12px", wordBreak: "break-all", color: "#222" },
    badgeContainer: { display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" },
    divider: { border: "none", borderTop: "1px solid #eee", margin: "16px 0" },
    sectionTitle: { fontSize: "14px", color: "#666", marginBottom: "8px" },
    summaryBox: { fontSize: "13px", lineHeight: "1.6", color: "#333", background: "#f9f9f9", padding: "12px", borderRadius: "8px" },
    repoSummaryBox: { marginTop: "20px", padding: "10px", background: "#eef2ff", borderRadius: "8px", fontSize: "13px", lineHeight: "1.5" },
    closeButton: { marginTop: "20px", width: "100%", padding: "12px", background: "#f3f4f6", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "600", color: "#555" },
    backButton: { marginTop: "20px", padding: "10px 20px", background: "#333", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }
};

function Badge({ color, label }) {
  if (!label) return null;
  const styleMap = {
      "bg-blue-100 text-blue-800": { backgroundColor: "#dbeafe", color: "#1e40af" },
      "bg-green-100 text-green-800": { backgroundColor: "#dcfce7", color: "#166534" },
      "bg-gray-100 text-gray-800": { backgroundColor: "#f3f4f6", color: "#1f2937" }
  };
  const style = styleMap[color] || { backgroundColor: "#eee", color: "#333" };
  return (
    <span style={{ padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "600", ...style }}>{label}</span>
  );
}