import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import { getArticle, getArticles } from '@/lib/server-api'

const SITE = process.env.SITE_URL ?? 'http://localhost'

interface Props {
  params: Promise<{ slug: string }>
}

// Pre-render nothing at build time; pages are generated on-demand (ISR)
export const dynamicParams = true

export async function generateStaticParams() {
  return []
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const article = await getArticle(slug)
  if (!article) return {}

  return {
    title: `${article.title} — Portfolio`,
    description: article.excerpt ?? undefined,
    openGraph: {
      title: article.title,
      description: article.excerpt ?? undefined,
      type: 'article',
      publishedTime: article.published_at ?? undefined,
      modifiedTime: article.updated_at,
      url: `${SITE}/blog/${slug}`,
    },
    twitter: {
      card: 'summary',
      title: article.title,
      description: article.excerpt ?? undefined,
    },
  }
}

export default async function ArticlePage({ params }: Props) {
  const { slug } = await params
  const article = await getArticle(slug)
  if (!article) notFound()

  const publishedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString('zh-TW', {
        year: 'numeric', month: 'long', day: 'numeric',
      })
    : null

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.excerpt,
    datePublished: article.published_at,
    dateModified: article.updated_at,
    url: `${SITE}/blog/${slug}`,
    author: { '@type': 'Person', name: 'Portfolio' },
  }

  return (
    <>
      <Header />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <main className="max-w-4xl mx-auto px-6 py-16">
        {/* Category */}
        {article.category && (
          <p className="text-xs text-sumi-light dark:text-dark-muted tracking-wide mb-4">
            {article.category.name}
          </p>
        )}

        {/* Title */}
        <h1 className="font-serif text-3xl text-sumi dark:text-washi leading-tight mb-4 tracking-wide">
          {article.title}
        </h1>

        {/* Meta */}
        <div className="flex items-center gap-4 mb-12 pb-8 border-b border-hairline dark:border-dark-border">
          {publishedDate && (
            <time className="text-xs text-sumi-light dark:text-dark-muted" dateTime={article.published_at ?? ''}>
              {publishedDate}
            </time>
          )}
          {article.tags.length > 0 && (
            <div className="flex gap-2">
              {article.tags.map(t => (
                <span key={t.id} className="text-xs text-sumi-light dark:text-dark-muted bg-washi-card dark:bg-dark-card px-2 py-0.5 rounded-full">
                  {t.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <MarkdownRenderer content={article.content_md ?? ''} />

        {/* Back */}
        <div className="mt-16 pt-8 border-t border-hairline dark:border-dark-border">
          <Link
            href="/blog"
            className="text-sm text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
          >
            ← 返回文章列表
          </Link>
        </div>
      </main>
      <Footer />
    </>
  )
}
