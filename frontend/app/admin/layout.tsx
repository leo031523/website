'use client'

import { ConfirmDialogProvider } from '@/components/admin/ConfirmDialog'
import { ToastProvider } from '@/components/admin/Toast'

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <ConfirmDialogProvider>{children}</ConfirmDialogProvider>
    </ToastProvider>
  )
}
