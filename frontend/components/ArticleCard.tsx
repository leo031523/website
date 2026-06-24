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
        <div className="flex-1 min-w-0">
          {article.category && (
            <Link
              href={`/blog/categories/${article.category.slug}`}
              className="text-xs text-sumi-light dark:text-dark-muted tracking-wide mb-2 block hover:text-ai dark:hover:text-dark-accent transition-colors"
              onClick={e => e.stopPropagation()}
            >
              {article.category.name}
            </Link>
          )}
          <h2 className="font-serif text-xl text-sumi dark:text-washi group-hover:text-ai dark:group-hover:text-dark-accent transition-colors leading-snug mb-2">
            {article.title}
          </h2>
          {showExcerpt && article.excerpt && (
            <p className="text-sm text-sumi-light dark:text-dark-muted leading-relaxed line-clamp-2">
              {article.excerpt}
            </p>
          )}
          <div className="flex items-center gap-3 mt-3">
            {date && (
              <time className="text-xs text-sumi-light dark:text-dark-muted" dateTime={article.published_at ?? ''}>
                {date}
              </time>
            )}
            {article.tags.length > 0 && (
              <div className="flex gap-1.5">
                {article.tags.map(t => (
                  <Link
                    key={t.id}
                    href={`/blog/tags/${t.slug}`}
                    onClick={e => e.stopPropagation()}
                    className="text-xs text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
                  >
                    #{t.name}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </Link>
    </article>
  )
}
