export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export interface Category {
  id: number
  name: string
  slug: string
}

export interface Tag {
  id: number
  name: string
  slug: string
}

export interface Tool {
  id: number
  name: string
  category: string | null
  url: string | null
  icon_url: string | null
  description: string | null
}

export interface MediaItem {
  id: number
  filename: string
  url: string
  mime_type: string
  size: number
  alt_text: string | null
  created_at: string
}

export interface Article {
  id: number
  title: string
  slug: string
  excerpt: string | null
  content_md?: string
  status: 'draft' | 'published'
  published_at: string | null
  author_id: number
  category: Category | null
  tags: Tag[]
  cover_image_id: number | null
  cover_image_url: string | null
  created_at: string
  updated_at: string
}

export interface ArticlePayload {
  title: string
  slug?: string
  excerpt?: string | null
  content_md: string
  status: 'draft' | 'published'
  category_id?: number | null
  tag_ids?: number[]
  cover_image_id?: number | null
}

export interface Project {
  id: number
  title: string
  slug: string
  summary: string | null
  content_md?: string
  tech_stack: string[]
  repo_url: string | null
  demo_url: string | null
  status: 'draft' | 'published'
  featured: boolean
  sort_order: number
  cover_image_id: number | null
  cover_image_url: string | null
  tags: Tag[]
  tools: Tool[]
  created_at: string
  updated_at: string
}

export interface ProjectPayload {
  title: string
  slug?: string
  summary?: string | null
  content_md?: string
  tech_stack?: string[]
  repo_url?: string | null
  demo_url?: string | null
  status?: 'draft' | 'published'
  featured?: boolean
  sort_order?: number
  tag_ids?: number[]
  tool_ids?: number[]
  cover_image_id?: number | null
}

export interface AboutContent {
  content_md: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
