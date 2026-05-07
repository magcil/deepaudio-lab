import client from '../api/client';

/**
 * Action service for triggering and configuring training jobs.
 * Use this to start a new training run or fetch available model/hardware options.
 * Completed training jobs appear as Run records retrievable via runService.
 */

/** Payload for starting a new training job. */
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

/** Response returned after submitting a training job. */
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


/** Available options for configuring a training job (backbones, pooling, GPUs). */
export interface TrainingOptions {
  backbones: string[];
  poolingMethods: string[];
  gpuIndexes: number[];
  cudaAvailable: boolean;
  mpsAvailable: boolean;
}

/** Fetches available training configuration options from the backend. */
export const getTrainingOptions = (): Promise<TrainingOptions> =>
  client.get<TrainingOptions>('/train/options');
