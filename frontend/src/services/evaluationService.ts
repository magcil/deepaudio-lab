import client from '../api/client';

export interface EvaluationPayload {
  evaluationData: string;
  classMapping: string;
  samplingRate?: number;
  segmentDuration: number | null;
  modelCheckpoint: string;
  numClasses: number;
  batchSize?: number;
  workers?: number;
  device: 'cpu' | 'gpu' | 'mps';
  gpuIndex: number | null;
}

export const startEvaluation = (payload: EvaluationPayload): Promise<void> =>
  client.post<void>('/evaluate/', payload);

export interface EvaluationOptions {
  gpuIndexes: number[];
  cudaAvailable: boolean;
  mpsAvailable: boolean;
}

export const getEvaluationOptions = (): Promise<EvaluationOptions> =>
  client.get<EvaluationOptions>('/evaluate/options');
