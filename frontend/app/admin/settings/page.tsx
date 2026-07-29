'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'

export default function SettingsPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

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
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (e) {
      setError(e instanceof Error ? e.message : '儲存失敗')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminShell title="帳號設定">
      <div className="flex flex-col gap-6 max-w-md">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-sumi-light tracking-wide">帳號</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-sumi-light tracking-wide">Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="pt-4 border-t border-hairline flex flex-col gap-1.5">
          <label className="text-xs text-sumi-light tracking-wide">新密碼（選填，留白則不更改）</label>
          <input
            type="password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        {newPassword && (
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light tracking-wide">確認新密碼</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
            />
          </div>
        )}

        <div className="pt-4 border-t border-hairline flex flex-col gap-1.5">
          <label className="text-xs text-sumi-light tracking-wide">目前密碼（確認身分才能儲存）</label>
          <input
            type="password"
            value={currentPassword}
            onChange={e => setCurrentPassword(e.target.value)}
            className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={save}
            disabled={saving}
            className="text-sm bg-ai text-washi px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50"
          >
            儲存
          </button>
          {saved && <span className="text-xs text-ai">已儲存 ✓</span>}
          {error && <span className="text-xs text-vermillion">{error}</span>}
        </div>
      </div>
    </AdminShell>
  )
}
