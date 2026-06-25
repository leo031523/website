import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import ArticleCard from '@/components/ArticleCard'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import { getArticles, getTagBySlug } from '@/lib/server-api'

interface Props {
  params: Promise<{ slug: string }>
}

export const dynamicParams = true
export async function generateStaticParams() { return [] }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const tag = await getTagBySlug(slug)
  if (!tag) return {}
  return {
    title: `#${tag.name} — Portfolio`,
    description: `標籤「${tag.name}」的所有文章`,
  }
}

export default async function TagPage({ params }: Props) {
  const { slug } = await params
  const tag = await getTagBySlug(slug)
  if (!tag) notFound()

  const data = await getArticles({ tag_id: tag.id, page_size: 100 })
  const articles = data.items

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <div className="mb-12">
          <Link href="/blog" className="text-xs text-sumi-light dark:text-dark-muted hover:text-ai transition-colors">
            ← 文章列表
          </Link>
          <h1 className="font-serif text-3xl text-sumi dark:text-washi mt-4 tracking-wide">
            #{tag.name}
          </h1>
          <p className="text-sm text-sumi-light dark:text-dark-muted mt-2">共 {articles.length} 篇</p>
        </div>

        {articles.length === 0 ? (
          <p className="text-sm text-sumi-light dark:text-dark-muted">此標籤尚無文章。</p>
        ) : (
          <div className="flex flex-col divide-y divide-hairline dark:divide-dark-border">
            {articles.map(a => (
              <div key={a.id} className="py-8 first:pt-0 last:pb-0">
                <ArticleCard article={a} />
              </div>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </>
  )
}
