import React, { useRef, useEffect } from "react";
import * as d3 from "d3";

const TreeGraph = ({ data, onNodeClick }) => {
  const svgRef = useRef();
  const wrapperRef = useRef();

  useEffect(() => {
    if (!data) return;

    // 1. 데이터 준비 (배열이 들어오면 가짜 루트로 감쌈)
    let rootData = data;
    if (Array.isArray(data)) {
      rootData = {
        id: "SYSTEM_ROOT",
        label: "System Root",
        type: "root",
        children: data,
      };
    }

    // 2. 캔버스 설정
    const width = wrapperRef.current ? wrapperRef.current.clientWidth : 800;
    const height = wrapperRef.current ? wrapperRef.current.clientHeight : 600;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    // 3. 줌 & 팬 설정
    const zoom = d3.zoom()
      .scaleExtent([0.1, 3])
      .on("zoom", (event) => g.attr("transform", event.transform));

    svg.call(zoom).on("dblclick.zoom", null);

    // 4. 트리 레이아웃 (간격 조정)
    const treeLayout = d3.tree().nodeSize([40, 250]); // 세로 40px, 가로 250px

    const root = d3.hierarchy(rootData);
    root.x0 = height / 2;
    root.y0 = 0;

    // 카드 크기
    const rectWidth = 180;
    const rectHeight = 36;

    // 5. 초기 접기 (루트 직계 자식까지만 노출)
    if (root.children) {
      root.children.forEach(collapse);
    }

    function collapse(d) {
      if (d.children) {
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
      }
    }

    // 초기 위치 (왼쪽 중앙)
    svg.call(zoom.transform, d3.zoomIdentity.translate(100, height / 2).scale(0.8));

    update(root);

    // 6. 업데이트 로직
    function update(source) {
      const treeData = treeLayout(root);
      const nodes = treeData.descendants();
      const links = treeData.links();

      // (A) 노드 바인딩 (ID 기준)
      const node = g.selectAll(".node")
        .data(nodes, (d) => d.data.id || d.id);

      // Enter
      const nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", (d) => `translate(${source.y0},${source.x0})`)
        .on("click", click)
        .style("cursor", (d) => (d.children || d._children ? "pointer" : "default"));

      // 카드 배경
      nodeEnter.append("rect")
        .attr("width", rectWidth)
        .attr("height", rectHeight)
        .attr("x", 0)
        .attr("y", -rectHeight / 2)
        .attr("rx", 6)
        .attr("ry", 6)
        .attr("stroke", "#fff")
        .style("fill", (d) => {
           if (d.data.type === "root") return "#2c3e50";
           return d.data.type === "directory" ? "#3498db" : "#27ae60"; 
        });

      // 아이콘
      nodeEnter.append("text")
        .attr("x", 12)
        .attr("y", 6)
        .style("font-size", "16px")
        .text((d) => {
            if (d.data.type === "root") return "🚀";
            return d.data.type === "directory" ? "📂" : "📄";
        });

      // 레이블
      nodeEnter.append("text")
        .attr("x", 38)
        .attr("y", 5)
        .style("font-size", "13px")
        .style("font-weight", "600")
        .style("fill", "white")
        .text((d) => {
            const label = d.data.label || d.data.id || "Unknown";
            return label.length > 20 ? label.substring(0, 20) + "..." : label;
        });

      // 힌트 원
      nodeEnter.append("circle")
        .attr("class", "toggle-hint")
        .attr("cx", rectWidth)
        .attr("cy", 0)
        .attr("r", 0)
        .style("fill", "white");

      // Update
      const nodeUpdate = nodeEnter.merge(node);
      nodeUpdate.transition().duration(250)
        .attr("transform", (d) => `translate(${d.y},${d.x})`);

      nodeUpdate.select("rect")
        .attr("stroke", (d) => d._children ? "#f1c40f" : "#fff")
        .attr("stroke-width", (d) => d._children ? 2 : 1);

      nodeUpdate.select(".toggle-hint")
        .attr("r", d => d._children ? 5 : 0);

      // Exit
      const nodeExit = node.exit().transition().duration(250)
        .attr("transform", (d) => `translate(${source.y},${source.x})`)
        .remove();
      nodeExit.select("rect").attr("width", 0).attr("height", 0);
      nodeExit.select("text").style("fill-opacity", 0);


      // (B) 링크 바인딩
      const link = g.selectAll(".link")
        .data(links, (d) => d.target.data.id || d.target.id);

      const diagonal = d3.linkHorizontal()
        .source((d) => ({ x: d.source.x, y: d.source.y + rectWidth })) // 카드 오른쪽 끝
        .target((d) => ({ x: d.target.x, y: d.target.y }))             // 카드 왼쪽 끝
        .x((d) => d.y)
        .y((d) => d.x);

      const linkEnter = link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("fill", "none")
        .attr("stroke", "#666")
        .attr("stroke-width", 1.5)
        .attr("d", (d) => {
          const o = { x: source.x0, y: source.y0 + rectWidth };
          const t = { x: source.x0, y: source.y0 };
          return d3.linkHorizontal().x(d => d.y).y(d => d.x)({ source: o, target: t });
        });

      linkEnter.merge(link).transition().duration(250).attr("d", diagonal);
      link.exit().transition().duration(250).remove();

      // 좌표 저장
      nodes.forEach((d) => {
        d.x0 = d.x;
        d.y0 = d.y;
      });
    }

    function click(event, d) {
      if (onNodeClick) onNodeClick(d.data); // 부모 연동
      if (!d.children && !d._children) return;

      if (d.children) {
        d._children = d.children;
        d.children = null;
      } else {
        d.children = d._children;
        d._children = null;
      }
      update(d);
    }
  }, [data, onNodeClick]);

  return (
    <div ref={wrapperRef} style={{ width: "100%", height: "100%", background: "#1e1e1e", overflow: "hidden", cursor: "grab" }}>
      <svg ref={svgRef} style={{ width: "100%", height: "100%" }}></svg>
    </div>
  );
};

export default TreeGraph;