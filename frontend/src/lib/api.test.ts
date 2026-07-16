import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, cvUrl, sendChat, SUGGESTED_QUESTIONS } from '@/lib/api'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('cvUrl', () => {
  it('builds a proxied PDF path', () => {
    expect(cvUrl('jane-doe.pdf')).toBe('/api/cvs/jane-doe.pdf')
    expect(cvUrl('folder/jane-doe.pdf')).toBe('/api/cvs/jane-doe.pdf')
  })
})

describe('sendChat', () => {
  it('rejects an empty question', async () => {
    await expect(sendChat({ question: '   ', history: [] })).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
    })
  })

  it('posts to /api/chat and returns the body', async () => {
    const payload = {
      answer: 'Jane Doe knows Python.',
      sources: [
        {
          candidateName: 'Jane Doe',
          file: 'jane-doe.pdf',
          section: 'Skills',
          snippet: 'Python',
          score: 0.9,
        },
      ],
      metrics: {
        provider: 'gemini',
        model: 'gemini-flash-latest',
        totalMs: 10,
        nodeTimingsMs: {},
        inputTokens: 1,
        outputTokens: 2,
        chunksRetrieved: 1,
        sourcesCited: 1,
        success: true,
      },
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    )

    const res = await sendChat({ question: 'Who knows Python?', history: [] })
    expect(res.answer).toContain('Jane Doe')
    expect(fetch).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('raises ApiError with detail from the response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        json: async () => ({ detail: 'Vector index is empty.' }),
      }),
    )

    await expect(sendChat({ question: 'Who?', history: [] })).rejects.toEqual(
      new ApiError('Vector index is empty.', 503),
    )
  })
})

describe('SUGGESTED_QUESTIONS', () => {
  it('includes the brief sample prompts', () => {
    expect(SUGGESTED_QUESTIONS).toContain('Who has experience with Python?')
    expect(SUGGESTED_QUESTIONS).toContain('Which candidate graduated from UPC?')
    expect(SUGGESTED_QUESTIONS).toContain('Summarize the profile of Jane Doe.')
  })
})
