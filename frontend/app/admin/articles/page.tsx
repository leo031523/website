'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { Article } from '@/lib/types'

export default function ArticleList() {
  const router = useRouter()
  const [articles, setArticles] = useState<Article[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listArticles({ page_size: 100 })
      .then(r => { setArticles(r.items); setTotal(r.total) })
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(id: number, title: string) {
    if (!confirm(`刪除「${title}」？此操作無法復原。`)) return
    await api.deleteArticle(id)
    setArticles(prev => prev.filter(a => a.id !== id))
    setTotal(t => t - 1)
  }

  return (
    <AdminShell title="文章管理">
      <div className="flex justify-between items-center mb-6">
        <p className="text-sm text-sumi-light">共 {total} 篇</p>
        <Link
          href="/admin/articles/new"
          className="text-sm bg-sumi text-washi px-4 py-2 rounded hover:bg-ai transition-colors"
        >
          + 新增文章
        </Link>
      </div>

      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : articles.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無文章，點擊右上角新增。</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide">標題</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-24">狀態</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-32">分類</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-28">更新時間</th>
              <th className="pb-3 w-20"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {articles.map(a => (
              <tr key={a.id} className="group">
                <td className="py-3 pr-4">
                  <Link
                    href={`/admin/articles/${a.id}`}
                    className="text-sumi hover:text-ai transition-colors"
                  >
                    {a.title}
                  </Link>
                </td>
                <td className="py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    a.status === 'published'
                      ? 'bg-ai/10 text-ai'
                      : 'bg-washi-card text-sumi-light'
                  }`}>
                    {a.status === 'published' ? '已發布' : '草稿'}
                  </span>
                </td>
                <td className="py-3 text-sumi-light">{a.category?.name ?? '—'}</td>
                <td className="py-3 text-sumi-light">
                  {new Date(a.updated_at).toLocaleDateString('zh-TW')}
                </td>
                <td className="py-3 text-right">
                  <button
                    onClick={() => handleDelete(a.id, a.title)}
                    className="text-xs text-sumi-light hover:text-vermillion transition-colors opacity-0 group-hover:opacity-100"
                  >
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
