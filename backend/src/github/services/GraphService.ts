import prisma from "../../prisma";

interface GraphNodeInput {
  id: string;
  label: string;
  type?: string;
  parent?: string | null;
  summary?: string;
  summary_details?: {
    logic?: string;
    intent?: string;
    structure?: string;
  };
  size?: number;
  color?: string;
  group?: string;
  domain?: string;
  importance?: number;
}

interface GraphEdgeInput {
  source: string;
  target: string;
  type: string;
  weight?: number;
}

interface GraphInput {
  nodes: GraphNodeInput[];
  edges: GraphEdgeInput[];
}

// 저장
export const saveGraphToDB = async (repoId: bigint, graph: GraphInput) => {
  const { nodes, edges } = graph;

  // 기존 그래프 삭제
  await prisma.graphEdge.deleteMany({ where: { repo_id: repoId } });
  await prisma.graphNode.deleteMany({ where: { repo_id: repoId } });
  await prisma.graph.deleteMany({ where: { repo_id: repoId } });

  // 그래프 생성
  const graphRow = await prisma.graph.create({
    data: { repo_id: repoId },
  });

  const graphId = graphRow.id;

  // 노드 생성
  const createdNodes = await Promise.all(
    nodes.map((node) =>
      prisma.graphNode.create({
        data: {
          repo_id: repoId,
          graphId,
          external_id: node.id,
          label: node.label,
          type: node.type ?? null,
          parent: node.parent ?? null,
          size: node.size ?? null,
          color: node.color ?? null,
          group: node.group ?? null,
          summary: node.summary ?? null,
          logic: node.summary_details?.logic ?? null,
          intent: node.summary_details?.intent ?? null,
          structure: node.summary_details?.structure ?? null,
          domain: node.domain ?? null,
          importance: node.importance ?? null,
        },
      })
    )
  );

  // external_id → DB id 매핑
  const idMap = new Map<string, bigint>();
  createdNodes.forEach((node) => idMap.set(node.external_id, node.id));

  // 엣지 생성
  await Promise.all(
    edges.map((edge) =>
      prisma.graphEdge.create({
        data: {
          repo_id: repoId,
          graphId,
          from_id: idMap.get(edge.source)!,
          to_id: idMap.get(edge.target)!,
          relation: edge.type,
          metadata: edge.weight ? { weight: edge.weight } : undefined,
        },
      })
    )
  );

  return { message: "Graph saved", nodeCount: nodes.length, edgeCount: edges.length };
};

// 조회
export const getGraphByRepoId = async (repoId: bigint) => {
  const graph = await prisma.graph.findUnique({
    where: { repo_id: repoId },
    include: { nodes: true, edges: true },
  });

  if (!graph) return { nodes: [], edges: [] };

  return {
    nodes: graph.nodes.map((n) => ({
      id: n.id,
      external_id: n.external_id,
      label: n.label,
      type: n.type,
      parent: n.parent,
      size: n.size,
      color: n.color,
      group: n.group,
      summary: n.summary,
      logic: n.logic,
      intent: n.intent,
      structure: n.structure,
      domain: n.domain,
      importance: n.importance,
    })),
    edges: graph.edges.map((e) => ({
      id: e.id,
      source: e.from_id,
      target: e.to_id,
      relation: e.relation,
      metadata: e.metadata,
    })),
  };
};
