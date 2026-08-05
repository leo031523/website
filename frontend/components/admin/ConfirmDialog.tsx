'use client'

import { createContext, useContext, useRef, useState } from 'react'

import { useFocusTrap } from './useFocusTrap'

interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>

const ConfirmContext = createContext<ConfirmFn | null>(null)

interface PendingConfirm {
  options: ConfirmOptions
  resolve: (result: boolean) => void
}

export function ConfirmDialogProvider({ children }: { children: React.ReactNode }) {
  const [pending, setPending] = useState<PendingConfirm | null>(null)
  const triggerRef = useRef<HTMLElement | null>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  function confirm(options: ConfirmOptions): Promise<boolean> {
    triggerRef.current = document.activeElement as HTMLElement
    return new Promise<boolean>(resolve => {
      setPending({ options, resolve })
    })
  }

  function close(result: boolean) {
    pending?.resolve(result)
    setPending(null)
    triggerRef.current?.focus?.()
  }

  useFocusTrap(dialogRef, !!pending, () => close(false))

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {pending && (
        <div
          className="fixed inset-0 z-[200] bg-black/40 flex items-center justify-center p-6"
          onClick={() => close(false)}
        >
          <div
            ref={dialogRef}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            aria-describedby="confirm-dialog-message"
            onClick={e => e.stopPropagation()}
            className="bg-white rounded-lg max-w-sm w-full p-6 shadow-lg"
          >
            <h2 id="confirm-dialog-title" className="font-serif text-lg text-sumi mb-2">
              {pending.options.title}
            </h2>
            <p id="confirm-dialog-message" className="text-sm text-sumi-light leading-relaxed mb-6">
              {pending.options.message}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => close(false)}
                className="text-sm px-4 py-2 rounded border border-hairline text-sumi hover:bg-washi-card transition-colors"
              >
                {pending.options.cancelLabel ?? '取消'}
              </button>
              <button
                onClick={() => close(true)}
                className={`text-sm px-4 py-2 rounded text-white transition-colors ${
                  pending.options.danger
                    ? 'bg-vermillion hover:bg-vermillion/80'
                    : 'bg-ai hover:bg-sumi'
                }`}
              >
                {pending.options.confirmLabel ?? '確定'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}

export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmContext)
  if (!ctx) throw new Error('useConfirm must be used within ConfirmDialogProvider')
  return ctx
}
