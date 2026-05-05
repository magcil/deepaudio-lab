import client from '../api/client';

export interface ActiveTask {
  task_id: string;
  run_id: number;
  experiment_name: string;
  task_type: 'train' | 'train_evaluation';
  created_at: string;
  /** Celery task state: PENDING | STARTED | PROGRESS | FAILURE */
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'FAILURE';
  info: Record<string, unknown> | null;
}

/** Fetches all active or failed Celery tasks. */
export const getActiveTasks = (): Promise<ActiveTask[]> =>
  client.get<ActiveTask[]>('/tasks/');
