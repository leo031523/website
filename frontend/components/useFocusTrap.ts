'use client'

import { useEffect } from 'react'

const FOCUSABLE_SELECTOR =
  'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'

/**
 * 對話框通用的鍵盤行為：開啟時把焦點移進去、Tab/Shift+Tab 在對話框內循環、
 * Escape 觸發關閉。不負責焦點還原 —— 呼叫端關閉時自行處理。
 */
export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement | null>,
  active: boolean,
  onEscape: () => void
) {
  useEffect(() => {
    if (!active) return
    const container = containerRef.current
    const initial = container?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    initial?.[0]?.focus()

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.preventDefault()
        onEscape()
        return
      }
      if (e.key === 'Tab') {
        const items = container?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
        if (!items || items.length === 0) return
        const first = items[0]
        const last = items[items.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active])
}
