import client from '../api/client';

export interface EvaluationPayload {
  testSet: string;
  trainRunId: number;
  batchSize?: number;
  workers?: number;
  device: 'cpu' | 'gpu' | 'mps';
  gpuIndex: number | null;
}

export interface StartEvaluationResponse {
  task_id: string;
}

export const startEvaluation = (payload: EvaluationPayload): Promise<StartEvaluationResponse> =>
  client.post<StartEvaluationResponse>('/evaluate/', payload);

export interface EvaluationOptions {
  gpuIndexes: number[];
  cudaAvailable: boolean;
  mpsAvailable: boolean;
}

export const getEvaluationOptions = (): Promise<EvaluationOptions> =>
  client.get<EvaluationOptions>('/evaluate/options');

export interface TrainRun {
  id: number;
  name: string;
  dataset_id: number | null;
}

export const getTrainRuns = (): Promise<TrainRun[]> =>
  client.get<TrainRun[]>('/runs/type/train');
