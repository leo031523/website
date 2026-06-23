'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { Article, MediaItem } from '@/lib/types'

export default function Dashboard() {
  const [articles, setArticles] = useState<Article[]>([])
  const [media, setMedia] = useState<MediaItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.listArticles({ page_size: 100 }),
      api.listMedia(),
    ]).then(([art, med]) => {
      setArticles(art.items)
      setMedia(med)
    }).finally(() => setLoading(false))
  }, [])

  const published = articles.filter(a => a.status === 'published').length
  const drafts = articles.filter(a => a.status === 'draft').length
  const recent = articles.slice(0, 5)

  return (
    <AdminShell title="儀表板">
      {loading ? (
        <p className="text-sumi-light text-sm">載入中…</p>
      ) : (
        <div className="flex flex-col gap-10">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="已發布文章" value={published} />
            <StatCard label="草稿" value={drafts} />
            <StatCard label="媒體檔案" value={media.length} />
          </div>

          {/* Recent articles */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-sumi-light uppercase tracking-widest">
                最近文章
              </h2>
              <Link href="/admin/articles/new" className="text-xs text-ai hover:underline">
                + 新增
              </Link>
            </div>
            {recent.length === 0 ? (
              <p className="text-sm text-sumi-light">尚無文章</p>
            ) : (
              <ul className="flex flex-col divide-y divide-hairline">
                {recent.map(a => (
                  <li key={a.id} className="py-3 flex items-center justify-between">
                    <Link
                      href={`/admin/articles/${a.id}`}
                      className="text-sm text-sumi hover:text-ai transition-colors"
                    >
                      {a.title}
                    </Link>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      a.status === 'published'
                        ? 'bg-ai/10 text-ai'
                        : 'bg-washi-card text-sumi-light'
                    }`}>
                      {a.status === 'published' ? '已發布' : '草稿'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </AdminShell>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-hairline rounded p-5 bg-white">
      <p className="text-3xl font-light text-sumi mb-1">{value}</p>
      <p className="text-xs text-sumi-light">{label}</p>
    </div>
  )
}
