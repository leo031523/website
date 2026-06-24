import type { MetadataRoute } from 'next'
import { getArticles } from '@/lib/server-api'

const SITE = process.env.SITE_URL ?? 'http://localhost'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const data = await getArticles({ page_size: 1000 })

  const articleEntries: MetadataRoute.Sitemap = data.items.map(a => ({
    url: `${SITE}/blog/${a.slug}`,
    lastModified: new Date(a.updated_at),
    changeFrequency: 'weekly',
    priority: 0.8,
  }))

  return [
    { url: `${SITE}/`, changeFrequency: 'weekly', priority: 1 },
    { url: `${SITE}/blog`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE}/about`, changeFrequency: 'monthly', priority: 0.5 },
    ...articleEntries,
  ]
}
