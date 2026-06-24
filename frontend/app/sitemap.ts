import type { MetadataRoute } from 'next'
import { getArticles, getProjects } from '@/lib/server-api'

const SITE = process.env.SITE_URL ?? 'http://localhost'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [articlesData, projects] = await Promise.all([
    getArticles({ page_size: 1000 }),
    getProjects(),
  ])

  const articleEntries: MetadataRoute.Sitemap = articlesData.items.map(a => ({
    url: `${SITE}/blog/${a.slug}`,
    lastModified: new Date(a.updated_at),
    changeFrequency: 'weekly',
    priority: 0.8,
  }))

  const projectEntries: MetadataRoute.Sitemap = projects.map(p => ({
    url: `${SITE}/projects/${p.slug}`,
    lastModified: new Date(p.updated_at),
    changeFrequency: 'monthly',
    priority: 0.7,
  }))

  return [
    { url: `${SITE}/`, changeFrequency: 'weekly', priority: 1 },
    { url: `${SITE}/blog`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE}/projects`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE}/about`, changeFrequency: 'monthly', priority: 0.5 },
    ...articleEntries,
    ...projectEntries,
  ]
}
