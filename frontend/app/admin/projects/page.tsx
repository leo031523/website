'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { Project } from '@/lib/types'

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listProjects().then(setProjects).finally(() => setLoading(false))
  }, [])

  async function handleDelete(id: number, title: string) {
    if (!confirm(`刪除「${title}」？`)) return
    await api.deleteProject(id)
    setProjects(prev => prev.filter(p => p.id !== id))
  }

  return (
    <AdminShell title="作品集">
      <div className="flex justify-between items-center mb-6">
        <p className="text-sm text-sumi-light">共 {projects.length} 件</p>
        <Link href="/admin/projects/new"
          className="text-sm bg-sumi text-washi px-4 py-2 rounded hover:bg-ai transition-colors">
          + 新增作品
        </Link>
      </div>

      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : projects.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無作品，點擊右上角新增。</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide">標題</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-16">精選</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-24">狀態</th>
              <th className="pb-3 text-xs text-sumi-light font-normal tracking-wide w-28">更新時間</th>
              <th className="pb-3 w-16"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {projects.map(p => (
              <tr key={p.id} className="group">
                <td className="py-3 pr-4">
                  <Link href={`/admin/projects/${p.id}`} className="text-sumi hover:text-ai transition-colors">
                    {p.title}
                  </Link>
                  {p.tech_stack.length > 0 && (
                    <span className="ml-2 text-xs text-sumi-light">
                      {p.tech_stack.slice(0, 3).join(', ')}
                    </span>
                  )}
                </td>
                <td className="py-3 text-center">
                  {p.featured && <span className="text-ai text-xs">★</span>}
                </td>
                <td className="py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    p.status === 'published' ? 'bg-ai/10 text-ai' : 'bg-washi-card text-sumi-light'
                  }`}>
                    {p.status === 'published' ? '已發布' : '草稿'}
                  </span>
                </td>
                <td className="py-3 text-sumi-light">
                  {new Date(p.updated_at).toLocaleDateString('zh-TW')}
                </td>
                <td className="py-3 text-right">
                  <button onClick={() => handleDelete(p.id, p.title)}
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
