import React, { useMemo, useRef, useState, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";

const CodeGraph = ({ data, onNodeClick, focusNode }) => { 
  const fgRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  const graphData = useMemo(() => {
    // 1. 데이터 존재 여부 확인
    if (!data || !data.graph) return { nodes: [], links: [] };
    
    // 🚨 [수정된 부분] 안전하게 배열 가져오기
    // nodes가 없으면 빈 배열 [], edges가 없으면 links 확인, 둘 다 없으면 빈 배열 []
    const rawNodes = data.graph.nodes || [];
    const rawLinks = data.graph.edges || data.graph.links || []; 

    // 2. 데이터 가공
    const nodes = rawNodes.map(node => ({ 
      ...node, 
      val: node.size ? Math.sqrt(node.size) / 2 : 5 
    }));
    
    const links = rawLinks.map(edge => ({ ...edge }));
    
    // 하이라이트용 이웃 찾기
    const neighbors = new Map();
    links.forEach(link => {
      const a = link.source.id || link.source;
      const b = link.target.id || link.target;
      if (!neighbors.has(a)) neighbors.set(a, []);
      if (!neighbors.has(b)) neighbors.set(b, []);
      neighbors.get(a).push(b);
      neighbors.get(b).push(a);
    });
    nodes.forEach(node => {
      node.neighbors = neighbors.get(node.id) || [];
    });
    return { nodes, links };
  }, [data]);

  // 검색 줌인
  useEffect(() => {
    if (focusNode && fgRef.current) {
      const node = graphData.nodes.find(n => n.id === focusNode.id);
      if (node && (node.x || node.x === 0)) {
        fgRef.current.centerAt(node.x, node.y, 1000);
        fgRef.current.zoom(3, 2000);
        handleNodeHover(node);
      }
    }
  }, [focusNode, graphData]);

  const handleNodeHover = (node) => {
    if ((!node && !highlightNodes.size) || (node && hoverNode === node)) return;
    setHoverNode(node || null);
    const newHighlightNodes = new Set();
    const newHighlightLinks = new Set();
    if (node) {
      newHighlightNodes.add(node.id);
      node.neighbors?.forEach(neighborId => newHighlightNodes.add(neighborId));
      graphData.links.forEach(link => {
        if (link.source.id === node.id || link.target.id === node.id) {
          newHighlightLinks.add(link);
        }
      });
    }
    setHighlightNodes(newHighlightNodes);
    setHighlightLinks(newHighlightLinks);
  };

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", background: "#1a1a1a", borderRadius: "12px", overflow: "hidden", position: "relative" }}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}

        d3VelocityDecay={0.3}
        warmupTicks={100}

        backgroundColor="#1a1a1a"
        
        // 링크 스타일
        linkColor={link => link.type === 'structure' ? "#444" : (hoverNode && !highlightLinks.has(link) ? "#333" : "#777")}
        linkWidth={link => link.type === 'structure' ? 0.5 : (hoverNode && highlightLinks.has(link) ? 2 : 1)}
        linkLineDash={link => link.type === 'structure' ? [2, 2] : null}
        linkDirectionalArrowLength={3.5}
        
        // 노드 렌더링
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.label || node.id;
          const fontSize = 12 / globalScale;
          const isHover = hoverNode === node;
          
          const isDirectory = node.type === 'directory' || node.type === 'root';
          
          let color = node.color;
          if (!color) {
             if (node.type === 'root') color = "#2c3e50";
             else if (node.type === 'directory') color = "#3498db"; 
             else color = "#2ecc71"; 
          }
          if (hoverNode && !highlightNodes.has(node.id)) color = "#333"; 

          ctx.beginPath();
          if (isDirectory) {
            const size = node.type === 'root' ? 16 : 12;
            ctx.fillStyle = isHover ? "#f1c40f" : color;
            ctx.fillRect(node.x - size/2, node.y - size/2, size, size);
          } else {
            const r = 4;
            ctx.fillStyle = isHover ? "#f1c40f" : color;
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
            ctx.fill();
          }

          if (globalScale > 1.5 || isHover || node.type === 'root') { 
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = isHover ? '#fff' : 'rgba(255, 255, 255, 0.7)';
            ctx.fillText(label, node.x, node.y + (isDirectory ? 12 : 8));
          }
        }}
        
        onNodeHover={handleNodeHover}
        onNodeClick={(node) => {
          onNodeClick && onNodeClick(node);
          fgRef.current.centerAt(node.x, node.y, 1000);
          fgRef.current.zoom(3, 2000);
        }}
      />
      <div style={{ position: "absolute", bottom: 10, left: 15, color: "#888", fontSize: "12px", pointerEvents: "none", zIndex: 10 }}>
        🖱️ <b>드래그</b>: 화면 이동 | <b>휠</b>: 확대/축소 | <b>클릭</b>: 선택
      </div>
    </div>
  );
};

export default CodeGraph;