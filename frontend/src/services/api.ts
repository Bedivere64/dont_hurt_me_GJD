const API_BASE = 'https://bedivere.space/api'

interface FetchOptions {
  method?: string
  body?: unknown
}

export async function fetchAPI<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }

  return response.json()
}

export async function getETFList(page = 1, perPage = 20) {
  return fetchAPI<{ items: any[]; total: number }>(`/etf/list?page=${page}&per_page=${perPage}`)
}

export async function getETFRanking(sortBy = 'tot_vol', limit = 10) {
  return fetchAPI<any[]>(`/etf/ranking?sort_by=${sortBy}&limit=${limit}`)
}

export async function getETFTrend(code: string, days = 30) {
  return fetchAPI<{ date: string; tot_vol: number; close_price: number }[]>(
    `/etf/${code}/trend?days=${days}`
  )
}

export async function compareETF(codes: string[], days = 30) {
  return fetchAPI<Record<string, any[]>>(`/etf/compare?codes=${codes.join(',')}&days=${days}`)
}
