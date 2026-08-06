'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { useFocusTrap } from '@/components/useFocusTrap'
import { api } from '@/lib/api'
import {
  buildHistoryPayload,
  clearConversation,
  loadConversation,
  saveConversation,
  type StoredChatMessage,
} from '@/lib/aiChatStorage'
import { AI_PROVIDER_LABELS, type AIProvider, type ChatHistoryMessage } from '@/lib/types'

type Status = 'loading' | 'available' | 'unavailable'

export default function AIAssistant() {
  const [status, setStatus] = useState<Status>('loading')
  const [provider, setProvider] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<StoredChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const triggerRef = useRef<HTMLButtonElement>(null)
  const drawerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const pendingHistoryRef = useRef<ChatHistoryMessage[]>([])
  const hydratedRef = useRef(false)

  useEffect(() => {
    api
      .aiStatus()
      .then(res => {
        setStatus(res.available ? 'available' : 'unavailable')
        setProvider(res.provider)
      })
      .catch(() => setStatus('unavailable'))
  }, [])

  useEffect(() => {
    setMessages(loadConversation())
    hydratedRef.current = true
  }, [])

  useEffect(() => {
    if (!hydratedRef.current) return
    saveConversation(messages)
  }, [messages])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  useFocusTrap(drawerRef, open, closeDrawer)

  function openDrawer() {
    setOpen(true)
  }

  function closeDrawer() {
    setOpen(false)
    abortRef.current?.abort()
    triggerRef.current?.focus()
  }

  async function sendMessage(text: string, isRetry = false) {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    if (isRetry) {
      setMessages(prev => (prev[prev.length - 1]?.error ? prev.slice(0, -1) : prev))
    } else {
      pendingHistoryRef.current = buildHistoryPayload(messages)
      setMessages(prev => [...prev, { role: 'user', content: trimmed }])
      setInput('')
    }
    setSending(true)

    const controller = new AbortController()
    abortRef.current = controller
    try {
      const res = await api.aiChat(trimmed, pendingHistoryRef.current, controller.signal)
      setMessages(prev => [...prev, { role: 'assistant', content: res.answer, sources: res.sources }])
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        // 使用者主動停止，不顯示錯誤訊息
      } else {
        const message = e instanceof Error ? e.message : '發生錯誤，請稍後再試'
        setMessages(prev => [...prev, { role: 'assistant', content: message, error: true }])
      }
    } finally {
      setSending(false)
      abortRef.current = null
    }
  }

  function handleStop() {
    abortRef.current?.abort()
  }

  function handleClear() {
    setMessages([])
    clearConversation()
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    sendMessage(input)
  }

  function handleRetry(text: string) {
    sendMessage(text, true)
  }

  const buttonLabel = status === 'unavailable' ? 'AI 助理（尚未開放）' : 'AI 助理'
  const providerLabel = provider ? (AI_PROVIDER_LABELS[provider as AIProvider] ?? provider) : null

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={openDrawer}
        aria-haspopup="dialog"
        aria-label={status === 'unavailable' ? 'AI 助理，目前尚未開放使用' : '開啟 AI 助理對話視窗'}
        className="text-sm text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors"
      >
        {buttonLabel}
      </button>

      {open && (
        <div className="fixed inset-0 z-[300] bg-black/40" onClick={closeDrawer}>
          <div
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="ai-assistant-title"
            onClick={e => e.stopPropagation()}
            className="fixed inset-y-0 right-0 w-full sm:w-[85vw] md:w-[420px] md:min-w-[320px] md:max-w-[480px] bg-washi dark:bg-dark-bg border-l border-hairline dark:border-dark-border shadow-lg flex flex-col"
          >
            <header className="flex items-center justify-between gap-3 px-5 py-4 border-b border-hairline dark:border-dark-border">
              <div className="min-w-0">
                <h2 id="ai-assistant-title" className="font-serif text-base text-sumi dark:text-washi">
                  AI 助理
                </h2>
                {status === 'available' && providerLabel && (
                  <p className="text-xs text-sumi-light dark:text-dark-muted mt-0.5">
                    你的訊息會傳送給 {providerLabel} 進行處理
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={messages.length === 0}
                  className="text-xs text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors disabled:opacity-40"
                >
                  清除對話
                </button>
                <button
                  type="button"
                  onClick={closeDrawer}
                  aria-label="關閉 AI 助理"
                  className="text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi text-sm"
                >
                  ✕
                </button>
              </div>
            </header>

            <div ref={listRef} className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4">
              {status === 'unavailable' && (
                <p className="text-sm text-sumi-light dark:text-dark-muted">
                  AI 助理目前尚未開放，敬請期待。
                </p>
              )}
              {status === 'available' && messages.length === 0 && (
                <p className="text-sm text-sumi-light dark:text-dark-muted">
                  你可以問我關於這個網站上文章或作品的問題。
                </p>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`flex flex-col gap-2 ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`max-w-[90%] rounded-lg px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                      m.role === 'user'
                        ? 'bg-ai text-white'
                        : m.error
                          ? 'bg-vermillion/10 text-vermillion border border-vermillion/30'
                          : 'bg-washi-card dark:bg-dark-card text-sumi dark:text-washi'
                    }`}
                  >
                    {m.content}
                  </div>
                  {m.error && (
                    <button
                      type="button"
                      onClick={() => {
                        const lastUser = [...messages.slice(0, i)].reverse().find(msg => msg.role === 'user')
                        if (lastUser) handleRetry(lastUser.content)
                      }}
                      className="text-xs text-ai dark:text-dark-accent hover:underline"
                    >
                      重試
                    </button>
                  )}
                  {m.sources && m.sources.length > 0 && (
                    <div className="flex flex-col gap-2 w-full max-w-[90%]">
                      {m.sources.map(s => (
                        <Link
                          key={s.id}
                          href={s.url}
                          className="block text-xs border border-hairline dark:border-dark-border rounded px-3 py-2 hover:border-ai dark:hover:border-dark-accent transition-colors"
                        >
                          <span className="block text-sumi dark:text-washi font-medium mb-1">{s.title}</span>
                          <span className="block text-sumi-light dark:text-dark-muted line-clamp-2">{s.snippet}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {sending && (
                <div className="flex items-center gap-2 text-sm text-sumi-light dark:text-dark-muted">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-sumi-light dark:bg-dark-muted animate-pulse" />
                  思考中…
                </div>
              )}
            </div>

            {status === 'available' && (
              <form onSubmit={handleSubmit} className="border-t border-hairline dark:border-dark-border p-4 flex items-end gap-2">
                <label htmlFor="ai-assistant-input" className="sr-only">
                  輸入訊息
                </label>
                <textarea
                  id="ai-assistant-input"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage(input)
                    }
                  }}
                  rows={1}
                  placeholder="輸入你的問題…"
                  disabled={sending}
                  maxLength={2000}
                  className="flex-1 resize-none rounded border border-hairline dark:border-dark-border bg-washi dark:bg-dark-bg text-sumi dark:text-washi text-sm px-3 py-2 focus:outline-none focus:border-ai dark:focus:border-dark-accent disabled:opacity-60"
                />
                {sending ? (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="text-xs px-4 py-2 rounded border border-hairline dark:border-dark-border text-sumi dark:text-washi hover:bg-washi-card dark:hover:bg-dark-card transition-colors shrink-0"
                  >
                    停止
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!input.trim()}
                    className="text-xs px-4 py-2 rounded bg-ai text-white hover:bg-sumi transition-colors disabled:opacity-40 shrink-0"
                  >
                    送出
                  </button>
                )}
              </form>
            )}
          </div>
        </div>
      )}
    </>
  )
}
