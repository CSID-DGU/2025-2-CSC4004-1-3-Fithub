// src/pages/GraphTest.js

import React, { useState, useMemo } from "react";
import CodeGraph from "../components/CodeGraph";
import TreeGraph from "../components/TreeGraph"; 
import { buildTree, flattenTreeToGraph } from "../utils/dataTransformer"; 
import rawData from "../data/verification_result.json"; 

export default function GraphTest() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  // --- 데이터 처리 ---
  const processedData = useMemo(() => {
    if (!rawData || !rawData.graph || !rawData.graph.nodes) {
        return { flat: null, nested: null };
    }
    
    // 1. 트리 생성 (폴더 자동 생성 & 압축)
    const nestedTree = buildTree(rawData.graph.nodes); 

    // 2. 트리를 다시 평면 그래프로 변환 (System Root 및 폴더 노드 포함됨)
    const flatGraphData = flattenTreeToGraph(nestedTree, rawData.graph.edges);

    return {
        // CodeGraph에는 구조가 포함된 평면 데이터를 전달
        flat: { graph: flatGraphData },  
        // TreeGraph에는 계층 데이터를 전달
        nested: nestedTree 
    };
  }, []); 


  // --- 검색 핸들러 ---
  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    
    // 검색은 변환된 그래프 노드에서 찾습니다.
    const nodes = processedData.flat?.graph?.nodes || [];
    const found = nodes.find(
      (node) => 
        (node.label && node.label.toLowerCase().includes(searchTerm.toLowerCase())) || 
        (node.id && node.id.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    if (found) {
      setSelectedNode(found);
      setSearchTerm("");
    } else {
      alert("❌ 해당 노드를 찾을 수 없습니다.");
    }
  };

  if (!processedData.flat) {
    return <div style={{ padding: "50px", textAlign: "center" }}>Loading...</div>;
  }

  return (
    <div style={{ width: "100%", minHeight: "100vh", padding: "20px", boxSizing: "border-box", background: "#f0f0f0", display: "flex", flexDirection: "column", alignItems: "center" }}>
      
      {/* 헤더 */}
      <header style={{ width: "100%", maxWidth: "1400px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0, fontSize: "24px", color: "#333" }}>🧪 Graph Visualization Dashboard</h1>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px" }}>
          <input type="text" placeholder="Search (ex: run.py)" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} style={{ padding: "10px 16px", borderRadius: "20px", border: "1px solid #ccc", width: "220px", outline: "none" }} />
          <button type="submit" style={{ background: "#333", color: "white", border: "none", padding: "10px 20px", borderRadius: "20px", cursor: "pointer", fontWeight: "bold" }}>Search</button>
        </form>
      </header>
      
      {/* 메인 컨텐츠 */}
      <div style={{ display: "flex", width: "100%", maxWidth: "1400px", height: "1200px", gap: "20px" }}>
        
        {/* 좌측: 그래프 영역 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "20px", minWidth: 0 }}>
          
          {/* A. 네트워크 그래프 */}
          <div style={{ flex: 1, background: "#1a1a1a", borderRadius: "16px", overflow: "hidden", boxShadow: "0 4px 20px rgba(0,0,0,0.15)", position: "relative" }}>
            <CodeGraph 
              data={processedData.flat} 
              onNodeClick={setSelectedNode} 
              focusNode={selectedNode}
            />
             <div style={{ position: "absolute", top: 15, left: 20, color: "white", fontWeight: "bold", zIndex: 10 }}>🕸️ Network View (Nodes & Folders)</div>
          </div>

          {/* B. 트리 그래프 */}
          <div style={{ flex: 1, background: "#1e1e1e", borderRadius: "16px", overflow: "hidden", boxShadow: "0 4px 20px rgba(0,0,0,0.15)", position: "relative" }}>
            <TreeGraph 
              data={processedData.nested} 
              onNodeClick={setSelectedNode} 
            />
            <div style={{ position: "absolute", top: 15, left: 20, color: "white", fontWeight: "bold", zIndex: 10, pointerEvents: "none" }}>🌳 Hierarchy View</div>
          </div>
        </div>

        {/* 우측: 상세 정보 패널 */}
        {selectedNode && (
          <div style={{ width: "400px", flexShrink: 0, height: "100%", background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)", overflowY: "auto", position: "sticky", top: 0 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "12px" }}>
              <span style={{ background: selectedNode.color || (selectedNode.type === 'directory' ? '#3498db' : '#2ecc71'), width: "12px", height: "12px", borderRadius: "50%", marginRight: "8px" }}/>
              <span style={{ fontSize: "12px", fontWeight: "bold", color: "#888", textTransform: "uppercase" }}>{selectedNode.type || "UNKNOWN"}</span>
            </div>
            <h2 style={{ fontSize: "20px", marginBottom: "12px", wordBreak: "break-all", color: "#222" }}>{selectedNode.label}</h2>
            
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "20px" }}>
              {selectedNode.importance && <Badge color="bg-blue-100 text-blue-800" label={`Imp: ${selectedNode.importance}`} />}
              <Badge color="bg-green-100 text-green-800" label={selectedNode.domain || "Common"} />
            </div>
            <hr style={{ border: "none", borderTop: "1px solid #eee", margin: "16px 0" }} />
            
            <h3 style={{ fontSize: "14px", color: "#666", marginBottom: "8px" }}>🧠 AI Summary</h3>
            <div style={{ fontSize: "13px", lineHeight: "1.6", color: "#333", background: "#f9f9f9", padding: "12px", borderRadius: "8px" }}>
              {selectedNode.summary || "요약 정보가 없습니다."}
            </div>
            <button onClick={() => setSelectedNode(null)} style={{ marginTop: "20px", width: "100%", padding: "12px", background: "#f3f4f6", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "600", color: "#555" }}>닫기</button>
          </div>
        )}
      </div>

      <style>{`
        .bg-blue-100 { background-color: #dbeafe; color: #1e40af; }
        .bg-green-100 { background-color: #dcfce7; color: #166534; }
        .bg-gray-100 { background-color: #f3f4f6; color: #1f2937; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
      `}</style>
    </div>
  );
}

function Badge({ color, label }) {
  if (!label) return null;
  return <span className={color} style={{ padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontWeight: "600" }}>{label}</span>;
}