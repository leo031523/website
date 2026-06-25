import type { Metadata } from 'next'
import Link from 'next/link'
import ArticleCard from '@/components/ArticleCard'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import { getArticles, getCategories } from '@/lib/server-api'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: '文章 — Portfolio',
  description: '技術筆記、工具心得與學習紀錄。',
}

const PAGE_SIZE = 10

interface Props {
  searchParams: Promise<{ page?: string; category?: string }>
}

export default async function BlogPage({ searchParams }: Props) {
  const { page: pageStr, category } = await searchParams
  const page = Math.max(1, Number(pageStr) || 1)
  const categoryId = category ? Number(category) : undefined

  const [data, categories] = await Promise.all([
    getArticles({ page, page_size: PAGE_SIZE, category_id: categoryId }),
    getCategories(),
  ])

  const { items, total, total_pages } = data

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="font-serif text-3xl text-sumi dark:text-washi mb-12 tracking-wide">文章</h1>

        {/* Category filter */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-10">
            <Link
              href="/blog"
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                !categoryId
                  ? 'border-sumi bg-sumi text-washi dark:border-dark-muted dark:bg-dark-card'
                  : 'border-hairline text-sumi-light hover:border-sumi hover:text-sumi dark:border-dark-border dark:text-dark-muted dark:hover:border-dark-muted dark:hover:text-washi'
              }`}
            >
              全部
            </Link>
            {categories.map(c => (
              <Link
                key={c.id}
                href={`/blog?category=${c.id}`}
                className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                  categoryId === c.id
                    ? 'border-sumi bg-sumi text-washi dark:border-dark-muted dark:bg-dark-card'
                    : 'border-hairline text-sumi-light hover:border-sumi hover:text-sumi dark:border-dark-border dark:text-dark-muted dark:hover:border-dark-muted dark:hover:text-washi'
                }`}
              >
                {c.name}
              </Link>
            ))}
          </div>
        )}

        {/* Article list */}
        {items.length === 0 ? (
          <p className="text-sumi-light dark:text-dark-muted text-sm">尚無文章。</p>
        ) : (
          <>
            <p className="text-xs text-sumi-light dark:text-dark-muted mb-8">共 {total} 篇</p>
            <div className="flex flex-col divide-y divide-hairline dark:divide-dark-border">
              {items.map(a => (
                <div key={a.id} className="py-8 first:pt-0 last:pb-0">
                  <ArticleCard article={a} />
                </div>
              ))}
            </div>

            {/* Pagination */}
            {total_pages > 1 && (
              <div className="flex justify-between mt-12">
                {page > 1 ? (
                  <Link
                    href={`/blog?page=${page - 1}${categoryId ? `&category=${categoryId}` : ''}`}
                    className="text-sm text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
                  >
                    ← 較新
                  </Link>
                ) : <span />}
                {page < total_pages && (
                  <Link
                    href={`/blog?page=${page + 1}${categoryId ? `&category=${categoryId}` : ''}`}
                    className="text-sm text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
                  >
                    較舊 →
                  </Link>
                )}
              </div>
            )}
          </>
        )}
      </main>
      <Footer />
    </>
  )
}
