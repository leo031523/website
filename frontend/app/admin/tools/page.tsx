'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { Tool } from '@/lib/types'

const EMPTY: Omit<Tool, 'id'> = { name: '', category: null, url: null, icon_url: null, description: null }

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.listTools().then(setTools).finally(() => setLoading(false))
  }, [])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) return
    setSaving(true)
    try {
      const tool = await api.createTool(form)
      setTools(prev => [...prev, tool])
      setForm(EMPTY)
    } finally { setSaving(false) }
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`刪除「${name}」？`)) return
    await api.deleteTool(id)
    setTools(prev => prev.filter(t => t.id !== id))
  }

  return (
    <AdminShell title="工具清單">
      {/* Add form */}
      <form onSubmit={handleAdd} className="border border-hairline rounded p-5 mb-8 bg-white">
        <p className="text-xs text-sumi-light uppercase tracking-widest mb-4">新增工具</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">名稱 *</label>
            <input type="text" required value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">分類</label>
            <input type="text" value={form.category ?? ''}
              onChange={e => setForm(f => ({ ...f, category: e.target.value || null }))}
              placeholder="語言、框架、工具…"
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">URL</label>
            <input type="url" value={form.url ?? ''}
              onChange={e => setForm(f => ({ ...f, url: e.target.value || null }))}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">說明</label>
            <input type="text" value={form.description ?? ''}
              onChange={e => setForm(f => ({ ...f, description: e.target.value || null }))}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
        </div>
        <button type="submit" disabled={saving}
          className="text-sm bg-sumi text-washi px-4 py-2 rounded hover:bg-ai transition-colors disabled:opacity-50">
          {saving ? '新增中…' : '新增工具'}
        </button>
      </form>

      {/* Tool list */}
      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : tools.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無工具，用上方表單新增。</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="pb-3 text-xs text-sumi-light font-normal">名稱</th>
              <th className="pb-3 text-xs text-sumi-light font-normal w-28">分類</th>
              <th className="pb-3 text-xs text-sumi-light font-normal">說明</th>
              <th className="pb-3 w-16"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {tools.map(t => (
              <tr key={t.id} className="group">
                <td className="py-3 pr-4">
                  {t.url ? (
                    <a href={t.url} target="_blank" rel="noopener noreferrer"
                      className="text-sumi hover:text-ai transition-colors">
                      {t.name}
                    </a>
                  ) : t.name}
                </td>
                <td className="py-3 text-sumi-light">{t.category ?? '—'}</td>
                <td className="py-3 text-sumi-light">{t.description ?? '—'}</td>
                <td className="py-3 text-right">
                  <button onClick={() => handleDelete(t.id, t.name)}
                    className="text-xs text-sumi-light hover:text-vermillion opacity-0 group-hover:opacity-100 transition-all">
                    刪除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </AdminShell>
  )
}
