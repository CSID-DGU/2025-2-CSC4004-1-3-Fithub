import axios from "axios";
import prisma from "../../prisma";

const AI_SERVER = process.env.AI_SERVER;

interface GenerateGraphParams {
  summaries: any[];
  embeddings: any[];
  contextMeta: any;
}

export const requestGraphFromAI = async (params: GenerateGraphParams) => {
  const { summaries, embeddings, contextMeta } = params;

  const response = await axios.post(`${AI_SERVER}/graph`, {
    summaries,
    embeddings,
    context_meta: contextMeta,
  });
  return response.data.final_graph;
};

//그래프를 DB(GraphNode / GraphEdge 모델)에 저장
export const saveGraphToDB = async (repoId: bigint, finalGraph: any) => {
  const { nodes, edges } = finalGraph;

  await prisma.graphEdge.deleteMany({ where: { repo_id: repoId } });
  await prisma.graphNode.deleteMany({ where: { repo_id: repoId } });

  //Node 저장
  const createdNodes = await Promise.all(
    nodes.map((node: any) =>
      prisma.graphNode.create({
        data: {
          repo_id: repoId,
          file_path: node.file_path ?? null,
          label: node.label,
          type: node.type ?? null,
          metadata: node.metadata || {},
        },
      })
    )
  );

  const nodeIdMap = new Map();
  nodes.forEach((originalNode: any, index: number) => {
    nodeIdMap.set(originalNode.id, createdNodes[index].id);
  });

  //Edge 저장
  await Promise.all(
    edges.map((edge: any) =>
      prisma.graphEdge.create({
        data: {
          repo_id: repoId,
          from_id: nodeIdMap.get(edge.from),
          to_id: nodeIdMap.get(edge.to),
          relation: edge.relation,
          metadata: edge.metadata || {},
        },
      })
    )
  );

  return { message: "Graph successfully saved to DB" };
};

//repoId로 Graph 조회
export const getGraphByRepoId = async (repoId: bigint) => {
  const nodes = await prisma.graphNode.findMany({
    where: { repo_id: repoId },
  });

  const edges = await prisma.graphEdge.findMany({
    where: { repo_id: repoId },
  });

  return {
    nodes: nodes.map((n) => ({
      id: n.id.toString(),
      label: n.label,
      type: n.type,
      file_path: n.file_path,
      metadata: n.metadata,
    })),
    edges: edges.map((e) => ({
      id: e.id.toString(),
      source: e.from_id.toString(),
      target: e.to_id.toString(),
      relation: e.relation,
      metadata: e.metadata,
    })),
  };
};

export const generateAndSaveGraph = async (repoId: bigint, params: GenerateGraphParams) => {
  const finalGraph = await requestGraphFromAI(params);
  await saveGraphToDB(repoId, finalGraph);
  
  return { message: "Graph generated & stored", repoId };
};
