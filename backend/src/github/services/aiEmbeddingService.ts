import axios from "axios";

const AI_SERVER = process.env.AI_SERVER;

interface GenerateEmbeddingsParams {
  summaries: any[];   
}

export const generateEmbeddings = async (params: GenerateEmbeddingsParams) => {
  const { summaries } = params;

  const response = await axios.post(`${AI_SERVER}/embeddings`, {
    summaries,
  });

  return response.data.embeddings; 
};

