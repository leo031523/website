import type { Article, ArticlePayload, Category, MediaItem, PaginatedResponse, Tag, User } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (res.status === 204) return undefined as T
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? `HTTP ${res.status}`)
  return data as T
}

export const api = {
  // ── Auth ────────────────────────────────────────────
  login: (username: string, password: string) =>
    req<{ user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  logout: () => req<void>('/auth/logout', { method: 'POST' }),

  getMe: () => req<User>('/auth/me'),

  // ── Articles ─────────────────────────────────────────
  listArticles: (params?: { page?: number; page_size?: number }) => {
    const q = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params ?? {}).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
      )
    )
    return req<PaginatedResponse<Article>>(`/articles?${q}`)
  },

  getArticleById: (id: number) => req<Article>(`/articles/id/${id}`),

  createArticle: (data: ArticlePayload) =>
    req<Article>('/articles', { method: 'POST', body: JSON.stringify(data) }),

  updateArticle: (id: number, data: Partial<ArticlePayload>) =>
    req<Article>(`/articles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteArticle: (id: number) =>
    req<void>(`/articles/${id}`, { method: 'DELETE' }),

  // ── Categories ───────────────────────────────────────
  listCategories: () => req<Category[]>('/categories'),

  createCategory: (data: { name: string; slug: string }) =>
    req<Category>('/categories', { method: 'POST', body: JSON.stringify(data) }),

  // ── Tags ─────────────────────────────────────────────
  listTags: () => req<Tag[]>('/tags'),

  createTag: (data: { name: string; slug: string }) =>
    req<Tag>('/tags', { method: 'POST', body: JSON.stringify(data) }),

  // ── Media ────────────────────────────────────────────
  listMedia: () => req<MediaItem[]>('/media'),

  uploadMedia: async (file: File): Promise<MediaItem> => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/media`, {
      method: 'POST',
      credentials: 'include',
      body: form,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data?.detail ?? `HTTP ${res.status}`)
    return data as MediaItem
  },

  deleteMedia: (id: number) => req<void>(`/media/${id}`, { method: 'DELETE' }),
}
