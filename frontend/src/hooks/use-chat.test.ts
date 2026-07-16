import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useChat } from '@/hooks/use-chat'
import { ApiError } from '@/lib/api'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    sendChat: vi.fn(),
  }
})

import { sendChat } from '@/lib/api'

const mockedSendChat = vi.mocked(sendChat)

afterEach(() => {
  vi.clearAllMocks()
})

describe('useChat', () => {
  it('appends user and assistant messages on success', async () => {
    mockedSendChat.mockResolvedValue({
      answer: 'Jane Doe knows Python.',
      sources: [],
      metrics: {
        provider: 'mock',
        totalMs: 1,
        nodeTimingsMs: {},
        inputTokens: 0,
        outputTokens: 0,
        chunksRetrieved: 0,
        sourcesCited: 0,
        success: true,
      },
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Who knows Python?')
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0]?.role).toBe('user')
    expect(result.current.messages[1]?.content).toContain('Jane Doe')
    expect(result.current.error).toBeNull()
  })

  it('sets error from ApiError and keeps the user message', async () => {
    mockedSendChat.mockRejectedValue(new ApiError('index empty', 503))

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Who?')
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.error).toBe('index empty')
  })

  it('sets a clear message on 429 quota errors', async () => {
    mockedSendChat.mockRejectedValue(
      new ApiError(
        'Gemini quota exceeded (free tier). Wait a minute and try again.',
        429,
      ),
    )

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Who?')
    })

    await waitFor(() => {
      expect(result.current.error).toMatch(/quota/i)
    })
  })

  it('ignores blank questions', async () => {
    const { result } = renderHook(() => useChat())
    await act(async () => {
      await result.current.ask('   ')
    })
    expect(mockedSendChat).not.toHaveBeenCalled()
    expect(result.current.messages).toHaveLength(0)
  })

  it('clear resets messages and error', async () => {
    mockedSendChat.mockRejectedValue(new ApiError('boom', 500))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Who?')
    })
    await waitFor(() => expect(result.current.error).toBe('boom'))

    act(() => {
      result.current.clear()
    })

    expect(result.current.messages).toHaveLength(0)
    expect(result.current.error).toBeNull()
  })
})
