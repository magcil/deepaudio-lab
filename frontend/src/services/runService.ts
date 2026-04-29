import client from '../api/client';

/**
 * Read-only service for fetching run records from the database.
 * A "run" is a historical record of either a training or evaluation job.
 * Runs created via trainingService or evaluationService are retrievable here.
 */

/** Summary record for a run (train or evaluation job). */

export interface Run {
  id: number;
  name: string;
  description: string | null;
  /** Whether this run was a training or evaluation job. */
  task_type: 'train' | 'evaluation';
  created_at: string;
  /** ID of the training run this evaluation was based on, if applicable. */
  parent_run_id: number | null;
}

/** Per-epoch loss value recorded during training. */
export interface Loss {
  epoch: number;
  split_type: 'train' | 'validation';
  loss: number;
}

/** Hyperparameters and paths used for a training job. */
export interface TrainParams {
  class_mapping: Record<string, string>;
  batch_size: number;
  num_workers: number;
  epochs: number;
  patience: number;
  lr: number;
  sample_rate: number;
  segment_duration: number | null;
  n_classes: number;
  backbone: string;
  pretrained_backbone: boolean;
  pooling: string;
  freeze_backbone: boolean;
  path_to_checkpoint: string;
  path_to_train: string;
  path_to_validation: string | null;
  device: string;
  gpu_index: number;
}

/** Parameters used for an evaluation job. */
export interface EvaluationParams {
  path_to_test: string;
  path_to_checkpoint: string;
  class_mapping: Record<string, string>;
}

/** Full run record including params, losses, and classification report. */
export interface RunDetail extends Run {
  train_params: TrainParams | null;
  evaluation_params: EvaluationParams | null;
  losses: Loss[];
  classification_report: Record<string, unknown> | null;
}

/** Fetches all runs (summary list). */
export const getRuns = (): Promise<Run[]> =>
  client.get<Run[]>('/runs/');

/** Fetches a single run with full details by ID. */
export const getRunById = (id: number): Promise<RunDetail> =>
  client.get<RunDetail>(`/runs/${id}`);
