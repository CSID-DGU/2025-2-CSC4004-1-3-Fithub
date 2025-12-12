// src/github/services/graphService.ts
import prisma from "../../prisma";

export const graphService = {

  async saveGraph(runId: string, repoId: bigint, graphData: any) {
    // 1) Graph 생성 (context, metrics 저장 X)
    const graph = await prisma.graph.create({
      data: {
        runId,
        repoId
      }
    });

    // 2) Nodes 저장
    if (Array.isArray(graphData.nodes)) {
      const nodeData = graphData.nodes.map((n: any) => ({
        graphId: graph.id,
        nodeId: n.id,
        label: n.label ?? null,
        type: n.type ?? null,
        parent: n.parent ?? null,
        domain: n.domain ?? null,
        importance: n.importance ?? null,
        summary: n.summary ?? null,
        summaryDetails: n.summary_details ?? null,
        context: n.context ?? null,
      }));
      await prisma.graphNode.createMany({ data: nodeData });
    }

    // 3) Edges 저장
    if (Array.isArray(graphData.edges)) {
      const edgeData = graphData.edges.map((e: any) => ({
        graphId: graph.id,
        source: e.source,
        target: e.target,
        type: e.type ?? null,
      }));
      await prisma.graphEdge.createMany({ data: edgeData });
    }

    return graph;
  },

  async getGraphByRunId(runId: string) {
    return prisma.graph.findFirst({
      where: { runId },
      include: {
        nodes: true,
        edges: true
      }
    });
  }

};
