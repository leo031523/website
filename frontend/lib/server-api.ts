import type { AboutContent, Article, Category, PaginatedResponse, Project, Tag } from './types'

const BASE = process.env.API_URL ?? 'http://backend:8000'

const EMPTY_PAGE: PaginatedResponse<Article> = {
  items: [], total: 0, page: 1, page_size: 10, total_pages: 0,
}

export async function getArticles(params?: {
  page?: number
  page_size?: number
  category_id?: number
  tag_id?: number
}): Promise<PaginatedResponse<Article>> {
  try {
    const q = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params ?? {})
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      )
    )
    const res = await fetch(`${BASE}/api/articles?${q}`, {
      next: { tags: ['articles'] },
    })
    if (!res.ok) return EMPTY_PAGE
    return res.json()
  } catch {
    return EMPTY_PAGE
  }
}

export async function getArticle(slug: string): Promise<Article | null> {
  try {
    const res = await fetch(`${BASE}/api/articles/${slug}`, {
      next: { tags: ['articles', `article-${slug}`] },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getCategories(): Promise<Category[]> {
  try {
    const res = await fetch(`${BASE}/api/categories`, {
      next: { tags: ['categories'] },
    })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function getCategoryBySlug(slug: string): Promise<Category | null> {
  const categories = await getCategories()
  return categories.find(c => c.slug === slug) ?? null
}

export async function getTags(): Promise<Tag[]> {
  try {
    const res = await fetch(`${BASE}/api/tags`, {
      next: { tags: ['tags'] },
    })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function getTagBySlug(slug: string): Promise<Tag | null> {
  const tags = await getTags()
  return tags.find(t => t.slug === slug) ?? null
}

export async function getProjects(): Promise<Project[]> {
  try {
    const res = await fetch(`${BASE}/api/projects`, {
      next: { tags: ['projects'] },
    })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function getProject(slug: string): Promise<Project | null> {
  try {
    const res = await fetch(`${BASE}/api/projects/${slug}`, {
      next: { tags: ['projects', `project-${slug}`] },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getAbout(): Promise<AboutContent | null> {
  try {
    const res = await fetch(`${BASE}/api/about`, {
      next: { tags: ['about'] },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}
