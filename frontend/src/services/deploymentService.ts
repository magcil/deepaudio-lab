import client from '../api/client';

export const createBundle = (runId: number, name: string): Promise<{ task_id: string }> =>
  client.post<{ task_id: string }>(`/runs/${runId}/deploy`, { name });

export const downloadBundle = async (runId: number): Promise<void> => {
  const { url } = await client.get<{ url: string }>(`/runs/${runId}/deploy/download`);
  window.open(url, '_blank');
};
