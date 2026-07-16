import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  RunMetrics,
  Source,
} from '@/types/api'

// flip to false when POST /api/chat exists
export const USE_MOCK = true

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const MOCK_METRICS: RunMetrics = {
  provider: 'mock',
  totalMs: 42,
  nodeTimingsMs: { retrieve: 12, generate: 30 },
  inputTokens: 120,
  outputTokens: 80,
  chunksRetrieved: 2,
  sourcesCited: 1,
  success: true,
}

const MOCK_SOURCES: Source[] = [
  {
    candidateName: 'Jane Doe',
    file: 'jane_doe.pdf',
    section: 'Skills',
    snippet: 'Python, FastAPI, and data pipelines for hiring tooling.',
    score: 0.91,
  },
  {
    candidateName: 'Jane Doe',
    file: 'jane_doe.pdf',
    section: 'Education',
    snippet: 'BSc Computer Science, Universitat Politècnica de Catalunya (UPC).',
    score: 0.87,
  },
]

function mockAnswer(question: string): ChatResponse {
  const q = question.toLowerCase()

  let answer: string
  let sources = MOCK_SOURCES

  if (q.includes('python')) {
    answer =
      'Jane Doe lists Python among her core skills, with FastAPI and data pipeline work.'
    sources = [MOCK_SOURCES[0]]
  } else if (q.includes('upc')) {
    answer =
      'Jane Doe graduated from Universitat Politècnica de Catalunya (UPC) with a BSc in Computer Science.'
    sources = [MOCK_SOURCES[1]]
  } else if (q.includes('jane')) {
    answer =
      'Jane Doe is a software engineer with Python/FastAPI experience and a CS degree from UPC.'
  } else {
    answer =
      'Based on the indexed CVs (mock), Jane Doe is a strong match for Python and UPC-related questions.'
  }

  return {
    answer,
    sources,
    metrics: {
      ...MOCK_METRICS,
      sourcesCited: sources.length,
      chunksRetrieved: sources.length,
    },
  }
}

async function delay(ms = 350): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms))
}

export async function getHealth(): Promise<HealthResponse> {
  if (USE_MOCK) {
    await delay(80)
    return { status: 'ok', indexReady: true }
  }

  const res = await fetch('/health')
  if (!res.ok) {
    throw new ApiError(`health failed: ${res.statusText}`, res.status)
  }
  return (await res.json()) as HealthResponse
}

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  if (!request.question.trim()) {
    throw new ApiError('question is required', 400)
  }

  if (USE_MOCK) {
    await delay()
    return mockAnswer(request.question)
  }

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail?: string }
      if (body.detail) detail = body.detail
    } catch {
      // keep statusText
    }
    throw new ApiError(detail, res.status)
  }

  return (await res.json()) as ChatResponse
}

export const SUGGESTED_QUESTIONS = [
  'Who has experience with Python?',
  'Which candidate graduated from UPC?',
  'Summarize the profile of Jane Doe.',
] as const
