import client from '../api/client';




// ------- For starting training job -------
export interface TrainingPayload {
  // Data config
  trainingData: string;
  classMapping: string | null;
  validationData: string | null;
  samplingRate?: number;
  segmentDuration: number | null;
  // Model settings
  backbone: string;
  pretrained: boolean;
  freezeBackbone: boolean;
  numClasses: number;
  checkpoint: string | null;
  // Hyperparameters
  epochs?: number;
  patience?: number;
  learningRate?: number;
  workers?: number;
  batchSize?: number;
  device: 'cpu' | 'gpu' | 'mps';
  gpuIndex: number | null;
}

export interface TrainingResponse {
  jobId: string;
  status: string;
  message: string;
}

// export const startTraining = (payload: TrainingPayload): Promise<TrainingResponse> =>
//   client.post<TrainingResponse>('/train', payload);

export interface StartTrainingResponse {
  task_id: string
}

export const startTraining = (payload: TrainingPayload): Promise<StartTrainingResponse> =>
  client.post<StartTrainingResponse>('/train/', payload);


// ---------- For fetching training options ----------

export interface TrainingOptions {
  backbones: string[];
  poolingMethods: string[];
  gpuIndexes: number[];
  cudaAvailable: boolean;
  mpsAvailable: boolean;
}

export const getTrainingOptions = (): Promise<TrainingOptions> =>
  client.get<TrainingOptions>('/train/options');
