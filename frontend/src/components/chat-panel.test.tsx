import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ChatPanel } from '@/components/chat-panel'
import { MessageBubble } from '@/components/message-bubble'
import { getHealth, sendChat } from '@/lib/api'

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
        model: 'gemini-flash-latest',
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

const mockedGetHealth = vi.mocked(getHealth)
const mockedSendChat = vi.mocked(sendChat)

beforeEach(() => {
  mockedGetHealth.mockResolvedValue({ status: 'ok', indexReady: true })
  localStorage.clear()
})

describe('MessageBubble', () => {
  it('renders grounded label for assistant replies', () => {
    render(
      <MessageBubble
        message={{
          id: '1',
          role: 'assistant',
          content: 'Jane Doe knows Python.',
          metrics: {
            provider: 'gemini',
            model: 'gemini-flash-lite-latest',
            totalMs: 12,
            nodeTimingsMs: {},
            inputTokens: 100,
            outputTokens: 40,
            chunksRetrieved: 1,
            sourcesCited: 1,
            success: true,
          },
        }}
      />,
    )
    expect(screen.getByText('Grounded answer')).toBeInTheDocument()
    expect(screen.getByText(/Jane Doe knows Python/)).toBeInTheDocument()
    expect(screen.getByTestId('answer-usage')).toHaveTextContent(
      'gemini-flash-lite-latest',
    )
    expect(screen.getByTestId('answer-usage')).toHaveTextContent('140 tokens')
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

    expect(screen.getByText('Ask the resume set')).toBeInTheDocument()
    expect(screen.getByLabelText('Chat model')).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: /Who has experience with Python/i }),
    )

    await waitFor(() => {
      expect(
        screen.getByText(/Jane Doe lists Python among her skills/),
      ).toBeInTheDocument()
    })
    expect(mockedSendChat).toHaveBeenCalledWith(
      expect.objectContaining({
        question: 'Who has experience with Python?',
        model: 'gemini-flash-latest',
      }),
    )
  })

  it('lets the user pick a model before asking', async () => {
    const user = userEvent.setup()
    render(<ChatPanel />)

    await waitFor(() => {
      expect(screen.getByLabelText('Chat model')).toBeInTheDocument()
    })

    await user.selectOptions(
      screen.getByLabelText('Chat model'),
      'gemini-flash-lite-latest',
    )
    await user.type(
      screen.getByRole('textbox', { name: 'Chat question' }),
      'Who knows React?',
    )
    await user.click(screen.getByRole('button', { name: 'Send' }))

    await waitFor(() => {
      expect(mockedSendChat).toHaveBeenCalledWith(
        expect.objectContaining({
          question: 'Who knows React?',
          model: 'gemini-flash-lite-latest',
        }),
      )
    })
  })

  it('locks chat and shows ingest CTA when index is empty', async () => {
    mockedGetHealth.mockResolvedValue({ status: 'ok', indexReady: false })
    const user = userEvent.setup()
    render(<ChatPanel />)

    await waitFor(() => {
      expect(screen.getByText('Index empty')).toBeInTheDocument()
    })

    expect(screen.getByText('Index not ready')).toBeInTheDocument()
    expect(screen.getByText(/python scripts\/ingest\.py/i)).toBeInTheDocument()
    expect(screen.queryByText('Ask the resume set')).not.toBeInTheDocument()

    const input = screen.getByRole('textbox', { name: 'Chat question' })
    expect(input).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()

    mockedGetHealth.mockResolvedValue({ status: 'ok', indexReady: true })
    await user.click(
      screen.getByRole('button', { name: /Refresh index status/i }),
    )

    await waitFor(() => {
      expect(screen.getByText('Grounded')).toBeInTheDocument()
    })
    expect(screen.getByText('Ask the resume set')).toBeInTheDocument()
    expect(input).not.toBeDisabled()
  })
})
