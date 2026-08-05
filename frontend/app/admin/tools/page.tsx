'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { useConfirm } from '@/components/admin/ConfirmDialog'
import { useToast } from '@/components/admin/Toast'
import { api } from '@/lib/api'
import type { Tool } from '@/lib/types'

const EMPTY: Omit<Tool, 'id'> = { name: '', category: null, url: null, icon_url: null, description: null }

export default function ToolsPage() {
  const confirm = useConfirm()
  const toast = useToast()
  const [tools, setTools] = useState<Tool[]>([])
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

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
      toast.success(`已新增工具「${tool.name}」`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '新增失敗')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: number, name: string) {
    const ok = await confirm({
      title: '刪除工具',
      message: `確定要刪除「${name}」嗎？此操作無法復原。`,
      confirmLabel: '刪除',
      danger: true,
    })
    if (!ok) return

    setDeletingId(id)
    try {
      await api.deleteTool(id)
      setTools(prev => prev.filter(t => t.id !== id))
      toast.success(`已刪除「${name}」`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '刪除失敗')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <AdminShell title="工具清單">
      {/* Add form */}
      <form onSubmit={handleAdd} className="border border-hairline rounded p-5 mb-8 bg-white">
        <p className="text-xs text-sumi-light uppercase tracking-widest mb-4">新增工具</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="tool-name" className="text-xs text-sumi-light">名稱 *</label>
            <input id="tool-name" name="name" type="text" required value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="tool-category" className="text-xs text-sumi-light">分類</label>
            <input id="tool-category" name="category" type="text" value={form.category ?? ''}
              onChange={e => setForm(f => ({ ...f, category: e.target.value || null }))}
              placeholder="語言、框架、工具…"
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="tool-url" className="text-xs text-sumi-light">URL</label>
            <input id="tool-url" name="url" type="url" value={form.url ?? ''}
              onChange={e => setForm(f => ({ ...f, url: e.target.value || null }))}
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="tool-description" className="text-xs text-sumi-light">說明</label>
            <input id="tool-description" name="description" type="text" value={form.description ?? ''}
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
                  <button
                    onClick={() => handleDelete(t.id, t.name)}
                    disabled={deletingId === t.id}
                    aria-label={`刪除工具「${t.name}」`}
                    className="text-xs text-sumi-light hover:text-vermillion opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-all disabled:opacity-50"
                  >
                    {deletingId === t.id ? '刪除中…' : '刪除'}
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
