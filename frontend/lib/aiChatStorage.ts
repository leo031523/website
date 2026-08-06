import type { ChatHistoryMessage, ChatSource } from './types'

const STORAGE_KEY = 'ai-chat-history'
const MAX_HISTORY_TURNS = 10
const MAX_HISTORY_TOTAL_CHARS = 8000

export interface StoredChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  error?: boolean
}

export function loadConversation(): StoredChatMessage[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveConversation(messages: StoredChatMessage[]): void {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  } catch {
    // sessionStorage 不可用（隱私模式等）時靜默放棄，不影響對話本身
  }
}

export function clearConversation(): void {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(STORAGE_KEY)
}

/** 把目前對話紀錄轉成送給後端的 history，符合後端上限（最多 10 則、總長 8000 字）。 */
export function buildHistoryPayload(messages: StoredChatMessage[]): ChatHistoryMessage[] {
  const turns = messages
    .filter(m => !m.error)
    .slice(-MAX_HISTORY_TURNS)
    .map(m => ({ role: m.role, content: m.content }))

  let totalChars = turns.reduce((sum, m) => sum + m.content.length, 0)
  while (turns.length > 0 && totalChars > MAX_HISTORY_TOTAL_CHARS) {
    const removed = turns.shift()
    totalChars -= removed?.content.length ?? 0
  }
  return turns
}
