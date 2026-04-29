import client from '../api/client';

export interface EvaluationPayload {
  evaluationData: string;
  batchSize?: number;
  workers?: number;
  device: 'cpu' | 'gpu';
  gpuIndex: number | null;
}

export const startEvaluation = (payload: EvaluationPayload): Promise<void> =>
  client.post<void>('/evaluate/', payload);

export interface EvaluationOptions {
  gpuIndexes: number[];
}

export const getEvaluationOptions = (): Promise<EvaluationOptions> =>
  client.get<EvaluationOptions>('/train/options');
