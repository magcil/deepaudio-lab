import client from '../api/client';

export interface TrainingPayload {
  // Data config
  trainingData: string;
  validationData: string | null;
  samplingRate: number;
  segmentDuration: number;
  // Model settings
  backbone: string;
  pretrained: boolean;
  freezeBackbone: boolean;
  modelSamplingRate: number;
  numClasses: number;
  checkpoint: string | null;
  // Hyperparameters
  epochs: number;
  patience: number;
  learningRate: number;
  workers: number;
  batchSize: number;
  device: 'cpu' | 'gpu';
  gpuIndex: number | null;
}

export interface TrainingResponse {
  jobId: string;
  status: string;
  message: string;
}

// export const startTraining = (payload: TrainingPayload): Promise<TrainingResponse> =>
//   client.post<TrainingResponse>('/train', payload);

export const startTraining = (payload: TrainingPayload): Promise<void> =>
  client.post<void>('/train', payload);
