'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { useToast } from '@/components/admin/Toast'
import { api } from '@/lib/api'

export default function SettingsPage() {
  const toast = useToast()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getMe().then(u => {
      setUsername(u.username)
      setEmail(u.email)
    })
  }, [])

  async function save() {
    setError('')
    if (!currentPassword) { setError('請輸入目前密碼以確認身分'); return }
    if (newPassword && newPassword !== confirmPassword) { setError('兩次輸入的新密碼不一致'); return }

    setSaving(true)
    try {
      await api.updateMe({
        username,
        email,
        current_password: currentPassword,
        new_password: newPassword || undefined,
      })
      toast.success('帳號設定已儲存')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (e) {
      const message = e instanceof Error ? e.message : '儲存失敗'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminShell title="帳號設定">
      <div className="flex flex-col gap-6 max-w-md">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="settings-username" className="text-xs text-sumi-light tracking-wide">帳號</label>
          <input
            id="settings-username"
            name="username"
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="settings-email" className="text-xs text-sumi-light tracking-wide">Email</label>
          <input
            id="settings-email"
            name="email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="pt-4 border-t border-hairline flex flex-col gap-1.5">
          <label htmlFor="settings-new-password" className="text-xs text-sumi-light tracking-wide">新密碼（選填，留白則不更改）</label>
          <input
            id="settings-new-password"
            name="new_password"
            type="password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        {newPassword && (
          <div className="flex flex-col gap-1.5">
            <label htmlFor="settings-confirm-password" className="text-xs text-sumi-light tracking-wide">確認新密碼</label>
            <input
              id="settings-confirm-password"
              name="confirm_password"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
            />
          </div>
        )}

        <div className="pt-4 border-t border-hairline flex flex-col gap-1.5">
          <label htmlFor="settings-current-password" className="text-xs text-sumi-light tracking-wide">目前密碼（確認身分才能儲存）</label>
          <input
            id="settings-current-password"
            name="current_password"
            type="password"
            value={currentPassword}
            onChange={e => setCurrentPassword(e.target.value)}
            aria-describedby={error ? 'settings-error' : undefined}
            aria-invalid={error ? true : undefined}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={save}
            disabled={saving}
            className="text-sm bg-ai text-washi px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50"
          >
            {saving ? '儲存中…' : '儲存'}
          </button>
          {error && (
            <span id="settings-error" role="alert" className="text-xs text-vermillion">
              {error}
            </span>
          )}
        </div>
      </div>
    </AdminShell>
  )
}
