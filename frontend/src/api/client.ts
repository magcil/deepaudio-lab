import keycloak from '../auth/keycloak'

export const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  await keycloak.updateToken(30)
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${keycloak.token}`,
  }
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: await authHeaders(),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function patch(path: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: await authHeaders(),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }
}

async function del(path: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: await authHeaders(),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || `HTTP ${response.status}`);
  }
}

const client = {
  get,
  post,
  patch,
  delete: del,
};

export default client;
