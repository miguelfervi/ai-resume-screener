import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ChatPanel } from '@/components/chat-panel'
import { MessageBubble } from '@/components/message-bubble'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    getHealth: vi.fn().mockResolvedValue({ status: 'ok', indexReady: true }),
    sendChat: vi.fn().mockResolvedValue({
      answer: 'Jane Doe lists Python among her skills.',
      sources: [
        {
          candidateName: 'Jane Doe',
          file: 'jane-doe.pdf',
          section: 'Skills',
          snippet: 'Python',
          score: 0.91,
        },
      ],
      metrics: {
        provider: 'mock',
        totalMs: 12,
        nodeTimingsMs: {},
        inputTokens: 1,
        outputTokens: 2,
        chunksRetrieved: 1,
        sourcesCited: 1,
        success: true,
      },
    }),
  }
})

describe('MessageBubble', () => {
  it('renders grounded label for assistant replies', () => {
    render(
      <MessageBubble
        message={{
          id: '1',
          role: 'assistant',
          content: 'Jane Doe knows Python.',
        }}
      />,
    )
    expect(screen.getByText('Grounded answer')).toBeInTheDocument()
    expect(screen.getByText(/Jane Doe knows Python/)).toBeInTheDocument()
  })

  it('renders user text without grounded label', () => {
    render(
      <MessageBubble
        message={{ id: '2', role: 'user', content: 'Who knows Python?' }}
      />,
    )
    expect(screen.queryByText('Grounded answer')).not.toBeInTheDocument()
    expect(screen.getByText('Who knows Python?')).toBeInTheDocument()
  })
})

describe('ChatPanel', () => {
  it('shows sample questions and submits one', async () => {
    const user = userEvent.setup()
    render(<ChatPanel />)

    await waitFor(() => {
      expect(screen.getByText('Grounded')).toBeInTheDocument()
    })

    expect(screen.getByText('Ask the résumé set')).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: /Who has experience with Python/i }),
    )

    await waitFor(() => {
      expect(
        screen.getByText(/Jane Doe lists Python among her skills/),
      ).toBeInTheDocument()
    })
  })
})
