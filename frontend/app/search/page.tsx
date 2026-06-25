'use client'

import { useState } from 'react'
import Link from 'next/link'
import Footer from '@/components/Footer'
import Header from '@/components/Header'

interface SearchResult {
  query: string
  articles: { id: number; title: string; slug: string; excerpt: string | null; published_at: string | null }[]
  projects: { id: number; title: string; slug: string; summary: string | null }[]
}

export default function SearchPage() {
  const [q, setQ] = useState('')
  const [result, setResult] = useState<SearchResult | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!q.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q.trim())}`, {
        credentials: 'include',
      })
      setResult(await res.json())
    } finally {
      setLoading(false)
    }
  }

  const total = (result?.articles.length ?? 0) + (result?.projects.length ?? 0)

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="font-serif text-3xl text-sumi dark:text-washi mb-10 tracking-wide">搜尋</h1>

        <form onSubmit={handleSearch} className="flex gap-3 mb-10">
          <input
            type="search"
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="輸入關鍵字…"
            autoFocus
            className="flex-1 border border-hairline dark:border-dark-border rounded px-4 py-2.5 text-sm text-sumi dark:text-washi bg-white dark:bg-dark-card focus:outline-none focus:border-ai dark:focus:border-dark-accent transition-colors"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-sumi dark:bg-dark-card text-washi dark:text-washi text-sm px-5 py-2.5 rounded hover:bg-ai transition-colors disabled:opacity-50"
          >
            {loading ? '搜尋中…' : '搜尋'}
          </button>
        </form>

        {result && (
          <div className="flex flex-col gap-10">
            <p className="text-xs text-sumi-light dark:text-dark-muted">
              「{result.query}」找到 {total} 筆結果
            </p>

            {result.articles.length > 0 && (
              <section>
                <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em] mb-5">文章</p>
                <ul className="flex flex-col divide-y divide-hairline dark:divide-dark-border">
                  {result.articles.map(a => (
                    <li key={a.id} className="py-4">
                      <Link href={`/blog/${a.slug}`}
                        className="font-serif text-sumi dark:text-washi hover:text-ai dark:hover:text-dark-accent transition-colors block mb-1">
                        {a.title}
                      </Link>
                      {a.excerpt && (
                        <p className="text-sm text-sumi-light dark:text-dark-muted line-clamp-1">{a.excerpt}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {result.projects.length > 0 && (
              <section>
                <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em] mb-5">作品</p>
                <ul className="flex flex-col divide-y divide-hairline dark:divide-dark-border">
                  {result.projects.map(p => (
                    <li key={p.id} className="py-4">
                      <Link href={`/projects/${p.slug}`}
                        className="font-serif text-sumi dark:text-washi hover:text-ai dark:hover:text-dark-accent transition-colors block mb-1">
                        {p.title}
                      </Link>
                      {p.summary && (
                        <p className="text-sm text-sumi-light dark:text-dark-muted line-clamp-1">{p.summary}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {total === 0 && (
              <p className="text-sm text-sumi-light dark:text-dark-muted">沒有找到符合的結果。</p>
            )}
          </div>
        )}
      </main>
      <Footer />
    </>
  )
}
