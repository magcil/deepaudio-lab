import client from '../api/client';

export interface Run {
  id: number;
  name: string;
  description: string | null;
  task_type: 'train' | 'evaluation';
  created_at: string;
  parent_run_id: number | null;
}

export interface Loss {
  epoch: number;
  split_type: 'train' | 'validation';
  loss: number;
}

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

export interface EvaluationParams {
  path_to_test: string;
  path_to_checkpoint: string;
  class_mapping: Record<string, string>;
}

export interface RunDetail extends Run {
  train_params: TrainParams | null;
  evaluation_params: EvaluationParams | null;
  losses: Loss[];
  classification_report: Record<string, unknown> | null;
}

export const getRuns = (): Promise<Run[]> =>
  client.get<Run[]>('/runs/');

export const getRunById = (id: number): Promise<RunDetail> =>
  client.get<RunDetail>(`/runs/${id}`);
