/** Keep in sync with backend/app/config.py CHAT_MODELS */
export const CHAT_MODELS = [
  {
    id: 'gemini-flash-latest',
    label: 'Flash',
    hint: 'Default',
  },
  {
    id: 'gemini-flash-lite-latest',
    label: 'Flash Lite',
    hint: 'Lighter',
  },
] as const

export type ChatModelId = (typeof CHAT_MODELS)[number]['id']

export const DEFAULT_CHAT_MODEL: ChatModelId = 'gemini-flash-latest'

const MODEL_STORAGE_KEY = 'chat-model-v1'

export function isChatModelId(value: string): value is ChatModelId {
  return CHAT_MODELS.some((m) => m.id === value)
}

export function readStoredChatModel(): ChatModelId {
  try {
    const raw = localStorage.getItem(MODEL_STORAGE_KEY)
    if (raw && isChatModelId(raw)) return raw
  } catch {
    /* ignore */
  }
  return DEFAULT_CHAT_MODEL
}

export function storeChatModel(model: ChatModelId): void {
  try {
    localStorage.setItem(MODEL_STORAGE_KEY, model)
  } catch {
    /* ignore */
  }
}
