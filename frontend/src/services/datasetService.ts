import client from '../api/client'

interface PresignedItem {
  path: string
  key: string
  url: string
}

interface PresignResponse {
  urls: PresignedItem[]
}

export function getPresignedUrls(paths: string[], user: string): Promise<PresignResponse> {
  return client.post<PresignResponse>('/datasets/presigned', { paths, user })
}

export async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
  const response = await fetch(url, { method: 'PUT', body: file, headers: { 'Content-Type': 'audio/wav' } })
  if (!response.ok) throw new Error(`Upload failed for ${file.name}: HTTP ${response.status}`)
}
