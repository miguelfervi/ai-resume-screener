import { ChatPanel } from '@/components/chat-panel'
import { ErrorBoundary } from '@/components/error-boundary'

function App() {
  return (
    <ErrorBoundary>
      <ChatPanel />
    </ErrorBoundary>
  )
}

export default App
