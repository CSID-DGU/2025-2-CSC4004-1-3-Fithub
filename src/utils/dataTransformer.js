/**
 * src/utils/dataTransformer.js
 */

/**
 * 1. 경로형 ID ("agent/utils.py")를 파싱하여 폴더 노드를 자동 생성하고,
 * 2. GitHub 스타일로 외동 폴더를 압축하여 트리 구조(Root)를 반환합니다.
 */
export function buildTree(nodes) {
  // 1. 루트 노드 정의
  const root = {
    id: "SYSTEM_ROOT",
    label: "System Root",
    type: "root",
    children: [],
  };

  const nodeMap = { "SYSTEM_ROOT": root };

  // 2. 경로 파싱 및 노드 생성
  nodes.forEach((rawNode) => {
    // ID가 "agent/core/run.py"라면 -> ["agent", "core", "run.py"]
    // (만약 ID가 경로가 아니라면 rawNode.path 등을 사용하도록 수정 필요)
    const parts = rawNode.id.split("/");
    
    let currentPath = "";
    let parentId = "SYSTEM_ROOT";

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1;
      currentPath = currentPath ? `${currentPath}/${part}` : part;

      if (!nodeMap[currentPath]) {
        // 노드가 없으면 생성
        if (isLast) {
          // A. 실제 파일 (원본 데이터 사용 + children 초기화)
          nodeMap[currentPath] = { ...rawNode, children: [] };
        } else {
          // B. 중간 폴더 (가짜 생성)
          nodeMap[currentPath] = {
            id: currentPath,
            label: part,
            type: "directory", // 타입 명시
            children: [],
            size: 0,
            color: null // 폴더 색상은 렌더링 시 결정
          };
        }

        // 부모와 연결
        const parentNode = nodeMap[parentId];
        if (parentNode) {
          parentNode.children.push(nodeMap[currentPath]);
        }
      } else {
        // 이미 노드가 있는 경우 (중복 처리)
        if (isLast) {
          Object.assign(nodeMap[currentPath], rawNode);
        }
      }

      // 다음 루프를 위해 부모 ID 갱신
      parentId = currentPath;
    });
  });

  // 3. 폴더 압축 (GitHub 스타일: a/b/c)
  compressNode(root);

  return root;
}

/**
 * 외동 폴더(자식이 폴더 하나뿐인 경우)를 부모와 합칩니다.
 */
function compressNode(node) {
  if (!node.children) return;

  node.children.forEach(compressNode);

  if (node.type !== "root" && node.children.length === 1) {
    const onlyChild = node.children[0];
    
    // 자식이 디렉토리인 경우에만 합침 (파일이면 합치지 않음)
    if (onlyChild.type === "directory") {
      node.label = `${node.label}/${onlyChild.label}`;
      node.id = onlyChild.id; 
      node.children = onlyChild.children;
      compressNode(node); // 재귀 검사
    }
  }
}

/**
 * - 트리 구조(Root)를 순회하여 ForceGraph용 평면 데이터({nodes, links})로 변환합니다.
 * - 폴더 구조(Structure)와 의존성(Dependency)을 모두 포함합니다.
 */
export function flattenTreeToGraph(rootNode, originalEdges = []) {
  const nodes = [];
  const links = [];

  // 1. 트리 순회: 노드 수집 & 구조적 링크 생성
  function traverse(node) {
    // ForceGraph용 노드 객체 생성 (children 참조 제거하여 순환 방지)
    const { children, _children, ...nodeProps } = node;
    nodes.push(nodeProps);

    if (node.children) {
      node.children.forEach((child) => {
        // 구조적 엣지: 부모 -> 자식
        links.push({
          source: node.id,
          target: child.id,
          type: "structure", // 선 종류 구분
        });
        traverse(child);
      });
    }
  }

  traverse(rootNode);

  // 2. 원본 의존성 링크(Imports 등) 추가
  const nodeIds = new Set(nodes.map(n => n.id));
  
  originalEdges.forEach(edge => {
    const sourceId = edge.source.id || edge.source;
    const targetId = edge.target.id || edge.target;

    if (nodeIds.has(sourceId) && nodeIds.has(targetId)) {
      links.push({
        source: sourceId,
        target: targetId,
        type: "dependency", // 선 종류 구분
        // 원본 엣지의 속성들(label 등)이 있다면 유지
        ...edge 
      });
    }
  });

  return { nodes, links };
}