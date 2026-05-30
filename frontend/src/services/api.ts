const API_BASE = 'https://bedivere.space/api'

interface FetchOptions {
  method?: string
  body?: unknown
}

interface ETFItem {
  sec_code: string
  sec_name: string
  full_name?: string
}

interface ETFListResponse {
  items: ETFItem[]
  total: number
}

interface ETFRankingItem {
  sec_code: string
  sec_name: string
  tot_vol: number
  stat_date: string
}

interface ETFTrendItem {
  date: string
  tot_vol: number
  close_price: number
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

export async function getETFList(page = 1, perPage = 20): Promise<ETFListResponse> {
  return fetchAPI<ETFListResponse>(`/etf/list?page=${page}&per_page=${perPage}`)
}

export async function getETFRanking(sortBy = 'tot_vol', limit = 10): Promise<ETFRankingItem[]> {
  return fetchAPI<ETFRankingItem[]>(`/etf/ranking?sort_by=${sortBy}&limit=${limit}`)
}

export async function getETFTrend(code: string, days = 30): Promise<ETFTrendItem[]> {
  return fetchAPI<ETFTrendItem[]>(`/etf/${code}/trend?days=${days}`)
}

export async function compareETF(codes: string[], days = 30): Promise<Record<string, ETFTrendItem[]>> {
  return fetchAPI<Record<string, ETFTrendItem[]>>(`/etf/compare?codes=${codes.join(',')}&days=${days}`)
}
