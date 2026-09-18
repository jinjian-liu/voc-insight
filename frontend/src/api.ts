export interface RuntimeSession {
  ready: boolean
  operator_name: string
  expires_at: string
}

export interface Feedback {
  id: number
  content: string
  source: string
  feedback_time: string
  product_module: string | null
  external_id: string | null
  note: string | null
  analysis_status: string
  created_by_name: string
  created_at: string
  analysis: Analysis | null
}

export interface Analysis {
  id: number
  feedback_id: number
  summary: string
  category: string
  subcategory: string | null
  keywords: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  severity: 'low' | 'medium' | 'high' | 'urgent'
  user_impact: string
  suggested_priority: 'P0' | 'P1' | 'P2' | 'P3'
  confidence: number
  information_missing: string[]
  model_name: string
  prompt_version: string
  confirmed: boolean
  confirmed_by_name: string | null
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

export interface Issue {
  id: number
  title: string
  description: string
  category: string
  status: 'pending' | 'processed'
  severity: 'low' | 'medium' | 'high' | 'urgent'
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  processed_by_name: string | null
  processed_at: string | null
  solution: string | null
  created_by_name: string
  created_at: string
  updated_at: string
  feedback_count: number
}

export interface IssueDetail extends Issue {
  feedbacks: Feedback[]
  activities: Array<{ id: number; action_type: string; comment: string | null; operator_name: string; created_at: string }>
}

export interface Category {
  id: number
  name: string
  description: string | null
  sort_order: number
}

export interface DashboardOverview {
  feedback_total: number
  feedback_pending_analysis: number
  issue_pending: number
  issue_processed: number
  high_severity_pending: number
  average_resolution_hours: number | null
  category_distribution: Array<{ name: string; value: number }>
  status_distribution: Array<{ name: string; value: number }>
  top_issues: Issue[]
}

export interface FeedbackPage {
  items: Feedback[]
  total: number
  page: number
  page_size: number
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `请求失败（${response.status}）`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  getSession: () => request<RuntimeSession>('/api/session'),
  createSession: (operatorName: string, apiKey: string) =>
    request<RuntimeSession>('/api/session', {
      method: 'POST',
      body: JSON.stringify({ operator_name: operatorName, api_key: apiKey }),
    }),
  clearSession: () => request<void>('/api/session', { method: 'DELETE' }),
  listFeedbacks: (params: URLSearchParams) =>
    request<FeedbackPage>(`/api/feedbacks?${params.toString()}`),
  createFeedback: (payload: Record<string, unknown>) =>
    request<Feedback>('/api/feedbacks', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  importFeedbacks: async (file: File) => {
    const body = new FormData()
    body.append('file', file)
    const response = await fetch('/api/feedbacks/import', { method: 'POST', credentials: 'include', body })
    const result = await response.json().catch(() => null)
    if (!response.ok) throw new Error(result?.detail || '导入失败')
    return result as { success: number; failed: number; errors: string[] }
  },
  getFeedback: (id: number) => request<Feedback>(`/api/feedbacks/${id}`),
  analyzeFeedback: (id: number) => request<{ status: string }>(`/api/feedbacks/${id}/analyze`, { method: 'POST' }),
  updateAnalysis: (feedbackId: number, payload: Record<string, unknown>) =>
    request<Analysis>(`/api/feedbacks/${feedbackId}/analysis`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteFeedback: (id: number) => request<void>(`/api/feedbacks/${id}`, { method: 'DELETE' }),
  listIssues: (params = new URLSearchParams()) => request<{ items: Issue[]; total: number }>(`/api/issues?${params}`),
  getIssue: (id: number) => request<IssueDetail>(`/api/issues/${id}`),
  createIssue: (payload: Record<string, unknown>) => request<Issue>('/api/issues', { method: 'POST', body: JSON.stringify(payload) }),
  findSimilarIssues: (title: string, category: string) => request<Array<Issue & { similarity_score: number }>>(`/api/issues/similar?${new URLSearchParams({ title, category })}`),
  linkFeedback: (issueId: number, feedbackId: number) => request<Issue>(`/api/issues/${issueId}/link`, { method: 'POST', body: JSON.stringify({ feedback_id: feedbackId }) }),
  completeIssue: (issueId: number, solution: string) => request<Issue>(`/api/issues/${issueId}/complete`, { method: 'POST', body: JSON.stringify({ solution }) }),
  updateIssue: (issueId: number, payload: Record<string, unknown>) => request<Issue>(`/api/issues/${issueId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteIssue: (issueId: number) => request<void>(`/api/issues/${issueId}`, { method: 'DELETE' }),
  listCategories: () => request<Category[]>('/api/categories'),
  createCategory: (payload: { name: string; description: string }) => request<Category>('/api/categories', { method: 'POST', body: JSON.stringify(payload) }),
  updateCategory: (id: number, payload: { name: string; description: string }) => request<Category>(`/api/categories/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteCategory: (id: number) => request<void>(`/api/categories/${id}`, { method: 'DELETE' }),
  getDashboard: () => request<DashboardOverview>('/api/dashboard/overview'),
}
