export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface ChatRequest {
  question: string
  history: ChatMessage[]
}

export interface Source {
  candidateName: string
  file: string
  section: string
  snippet: string
  score: number
}

export interface RunMetrics {
  provider: string
  totalMs: number
  nodeTimingsMs: Record<string, number>
  inputTokens: number
  outputTokens: number
  chunksRetrieved: number
  sourcesCited: number
  success: boolean
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  metrics: RunMetrics
}

export interface HealthResponse {
  status: string
  indexReady: boolean
}
