import axios from 'axios';

const AI_AGENT_URL = process.env.AI_AGENT_URL || 'http://localhost:8000';

export interface AnalysisResult {
    run_id: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    result?: any;
    error?: string;
}

export class AIService {
    /**
     * Trigger a new analysis for a repository.
     * @param repoUrl The URL of the GitHub repository.
     * @param options Optional analysis options.
     */
    static async analyzeRepository(repoUrl: string, options: any = {}): Promise<string> {
        try {
            const response = await axios.post(`${AI_AGENT_URL}/analyze`, {
                repo: {
                    url: repoUrl,
                    branch: options.branch || 'main'
                },
                options: options
            });
            return response.data.run_id;
        } catch (error) {
            console.error('Error triggering analysis:', error);
            throw new Error('Failed to trigger analysis');
        }
    }

    /**
     * Get the status and result of an analysis.
     * @param runId The ID of the analysis run.
     */
    static async getAnalysisResult(runId: string): Promise<AnalysisResult> {
        try {
            const response = await axios.get(`${AI_AGENT_URL}/result/${runId}`);
            return response.data;
        } catch (error) {
            console.error(`Error getting result for run ${runId}:`, error);
            throw new Error('Failed to get analysis result');
        }
    }

    /**
     * Polls the analysis result until completion or failure.
     * @param runId The ID of the analysis run.
     * @param intervalMs Polling interval in milliseconds.
     * @param timeoutMs Max timeout in milliseconds.
     */
    static async pollAnalysisResult(runId: string, intervalMs: number = 2000, timeoutMs: number = 600000): Promise<AnalysisResult> {
        const startTime = Date.now();

        return new Promise((resolve, reject) => {
            const checkStatus = async () => {
                try {
                    const result = await this.getAnalysisResult(runId);

                    if (result.status === 'completed' || result.status === 'failed') {
                        resolve(result);
                        return;
                    }

                    if (Date.now() - startTime > timeoutMs) {
                        reject(new Error('Analysis polling timed out'));
                        return;
                    }

                    setTimeout(checkStatus, intervalMs);
                } catch (error) {
                    reject(error);
                }
            };

            checkStatus();
        });
    }
}
