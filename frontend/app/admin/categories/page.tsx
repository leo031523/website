'use client'

import { useEffect, useState } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { Category } from '@/lib/types'

function toSlug(name: string) {
  return name.toLowerCase().trim().replace(/\s+/g, '-').replace(/[^\w-]/g, '')
}

function hasChinese(s: string) {
  return /[一-鿿]/.test(s)
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [slugEdited, setSlugEdited] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editSlug, setEditSlug] = useState('')
  const [openMenuId, setOpenMenuId] = useState<number | null>(null)

  useEffect(() => {
    api.listCategories().then(setCategories).finally(() => setLoading(false))
  }, [])

  function handleNameChange(v: string) {
    setName(v)
    if (!slugEdited && !hasChinese(v)) setSlug(toSlug(v))
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !slug.trim()) return
    setSaving(true)
    try {
      const cat = await api.createCategory({ name: name.trim(), slug: slug.trim() })
      setCategories(prev => [...prev, cat])
      setName('')
      setSlug('')
      setSlugEdited(false)
    } finally { setSaving(false) }
  }

  async function handleDelete(id: number, catName: string) {
    if (!confirm(`刪除分類「${catName}」？（不會刪除旗下文章，僅解除關聯）`)) return
    await api.deleteCategory(id)
    setCategories(prev => prev.filter(c => c.id !== id))
  }

  function startEdit(cat: Category) {
    setEditId(cat.id)
    setEditName(cat.name)
    setEditSlug(cat.slug)
    setOpenMenuId(null)
  }

  async function handleSaveEdit(id: number) {
    if (!editName.trim() || !editSlug.trim()) return
    await api.updateCategory(id, { name: editName.trim(), slug: editSlug.trim() })
    setCategories(prev => prev.map(c => c.id === id ? { ...c, name: editName.trim(), slug: editSlug.trim() } : c))
    setEditId(null)
  }

  return (
    <AdminShell title="分類管理">
      <form onSubmit={handleAdd} className="border border-hairline rounded p-5 mb-8 bg-white">
        <p className="text-xs text-sumi-light uppercase tracking-widest mb-4">新增分類</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">名稱 *</label>
            <input
              type="text" required value={name}
              onChange={e => handleNameChange(e.target.value)}
              placeholder="例：技術筆記"
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light">Slug * <span className="text-hairline">（網址用）</span></label>
            <input
              type="text" required value={slug}
              onChange={e => { setSlug(e.target.value); setSlugEdited(true) }}
              placeholder="例：tech-notes"
              className="border border-hairline rounded px-3 py-2 text-sm focus:outline-none focus:border-ai font-mono"
            />
          </div>
        </div>
        <button type="submit" disabled={saving}
          className="text-sm bg-sumi text-washi px-4 py-2 rounded hover:bg-ai transition-colors disabled:opacity-50">
          {saving ? '新增中…' : '新增分類'}
        </button>
      </form>

      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : categories.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無分類，用上方表單新增。</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="pb-3 text-xs text-sumi-light font-normal">名稱</th>
              <th className="pb-3 text-xs text-sumi-light font-normal">Slug</th>
              <th className="pb-3 w-8"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {categories.map(cat => (
              <tr key={cat.id}>
                {editId === cat.id ? (
                  <>
                    <td className="py-2 pr-4">
                      <input value={editName} onChange={e => setEditName(e.target.value)}
                        autoFocus
                        className="border border-hairline rounded px-2 py-1 text-sm focus:outline-none focus:border-ai w-full" />
                    </td>
                    <td className="py-2 pr-4">
                      <input value={editSlug} onChange={e => setEditSlug(e.target.value)}
                        className="border border-hairline rounded px-2 py-1 text-sm focus:outline-none focus:border-ai w-full font-mono" />
                    </td>
                    <td className="py-2">
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => handleSaveEdit(cat.id)}
                          className="text-xs text-ai hover:text-sumi transition-colors">儲存</button>
                        <button onClick={() => setEditId(null)}
                          className="text-xs text-sumi-light hover:text-sumi transition-colors">取消</button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="py-3 pr-4 text-sumi">{cat.name}</td>
                    <td className="py-3 pr-4 text-sumi-light font-mono text-xs">{cat.slug}</td>
                    <td className="py-3 relative">
                      <button
                        onClick={() => setOpenMenuId(openMenuId === cat.id ? null : cat.id)}
                        className="text-sumi-light hover:text-sumi transition-colors px-1 leading-none text-base"
                        aria-label="選單"
                      >
                        ⋯
                      </button>
                      {openMenuId === cat.id && (
                        <>
                          <div className="fixed inset-0 z-10" onClick={() => setOpenMenuId(null)} />
                          <div className="absolute right-0 top-9 z-20 bg-white border border-hairline rounded shadow-sm py-1 w-24">
                            <button
                              onClick={() => startEdit(cat)}
                              className="block w-full text-left px-3 py-1.5 text-xs text-sumi hover:bg-washi-card transition-colors"
                            >
                              改名
                            </button>
                            <button
                              onClick={() => { navigator.clipboard.writeText(cat.name); setOpenMenuId(null) }}
                              className="block w-full text-left px-3 py-1.5 text-xs text-sumi hover:bg-washi-card transition-colors"
                            >
                              複製名稱
                            </button>
                            <button
                              onClick={() => { setOpenMenuId(null); handleDelete(cat.id, cat.name) }}
                              className="block w-full text-left px-3 py-1.5 text-xs text-vermillion hover:bg-washi-card transition-colors"
                            >
                              刪除
                            </button>
                          </div>
                        </>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </AdminShell>
  )
}
