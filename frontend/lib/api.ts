import type { Article, ArticlePayload, Category, MediaItem, PaginatedResponse, Project, ProjectPayload, Tag, Tool, User } from './types'

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

  updateCategory: (id: number, data: { name: string; slug: string }) =>
    req<Category>(`/categories/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteCategory: (id: number) => req<void>(`/categories/${id}`, { method: 'DELETE' }),

  // ── Tags ─────────────────────────────────────────────
  listTags: () => req<Tag[]>('/tags'),

  createTag: (data: { name: string; slug: string }) =>
    req<Tag>('/tags', { method: 'POST', body: JSON.stringify(data) }),

  updateTag: (id: number, data: { name: string; slug: string }) =>
    req<Tag>(`/tags/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteTag: (id: number) => req<void>(`/tags/${id}`, { method: 'DELETE' }),

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

  updateMedia: (id: number, data: { alt_text: string | null }) =>
    req<MediaItem>(`/media/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  deleteMedia: (id: number) => req<void>(`/media/${id}`, { method: 'DELETE' }),

  // ── Projects ─────────────────────────────────────────
  listProjects: () => req<Project[]>('/projects'),

  getProjectById: (id: number) => req<Project>(`/projects/id/${id}`),

  createProject: (data: ProjectPayload) =>
    req<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),

  updateProject: (id: number, data: Partial<ProjectPayload>) =>
    req<Project>(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteProject: (id: number) => req<void>(`/projects/${id}`, { method: 'DELETE' }),

  // ── Tools ────────────────────────────────────────────
  listTools: () => req<Tool[]>('/tools'),

  createTool: (data: Omit<Tool, 'id'>) =>
    req<Tool>('/tools', { method: 'POST', body: JSON.stringify(data) }),

  updateTool: (id: number, data: Partial<Omit<Tool, 'id'>>) =>
    req<Tool>(`/tools/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteTool: (id: number) => req<void>(`/tools/${id}`, { method: 'DELETE' }),
}
