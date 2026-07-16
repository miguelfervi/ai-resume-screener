import { Component, type ErrorInfo, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'

type Props = {
  children: ReactNode
}

type State = {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Chat UI crashed', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="chat-shell flex min-h-dvh flex-col items-center justify-center px-6 text-center">
          <p className="font-heading text-2xl tracking-tight">Something broke</p>
          <p className="text-muted-foreground mt-2 max-w-sm text-sm">
            {this.state.error.message || 'Unexpected render error in the chat UI.'}
          </p>
          <Button
            type="button"
            className="mt-6"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}
