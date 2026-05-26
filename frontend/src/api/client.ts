export const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data as T;
}

async function del(path: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }
}

const client = {
  get,
  post,
  delete: del,
};

export default client;
