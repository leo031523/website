import Link from 'next/link'
import type { Article } from '@/lib/types'

interface Props {
  article: Article
  showExcerpt?: boolean
}

export default function ArticleCard({ article, showExcerpt = true }: Props) {
  const date = article.published_at
    ? new Date(article.published_at).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  return (
    <article className="group">
      <Link href={`/blog/${article.slug}`} className="block">
        <div className="flex items-start gap-4">
          <div className="flex-1 min-w-0">
            {article.category && (
              <span className="text-xs text-sumi-light tracking-wide mb-2 block">
                {article.category.name}
              </span>
            )}
            <h2 className="font-serif text-xl text-sumi group-hover:text-ai transition-colors leading-snug mb-2">
              {article.title}
            </h2>
            {showExcerpt && article.excerpt && (
              <p className="text-sm text-sumi-light leading-relaxed line-clamp-2">
                {article.excerpt}
              </p>
            )}
            {date && (
              <time className="text-xs text-sumi-light mt-3 block" dateTime={article.published_at ?? ''}>
                {date}
              </time>
            )}
          </div>
        </div>
      </Link>
    </article>
  )
}
