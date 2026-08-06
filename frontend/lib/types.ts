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

export type AIProvider = 'gemini' | 'openai' | 'claude' | 'openai_compatible'

export const AI_PROVIDER_LABELS: Record<AIProvider, string> = {
  gemini: 'Google Gemini',
  openai: 'OpenAI',
  claude: 'Anthropic Claude',
  openai_compatible: 'OpenAI 相容服務',
}

// 四種 provider 都已經有後端 adapter 實作，全部可以啟用／測試連線。
export const AI_SUPPORTED_PROVIDERS: readonly AIProvider[] = ['gemini', 'openai', 'claude', 'openai_compatible']

export interface AIProviderSettings {
  id: number
  provider: AIProvider
  model: string
  base_url: string | null
  is_configured: boolean
  api_key_suffix: string | null
  is_enabled: boolean
  timeout_seconds: number
  max_output_tokens: number
  top_k: number
  created_at: string
  updated_at: string
}

export interface AIProviderSettingsPayload {
  provider: AIProvider
  model: string
  base_url?: string | null
  api_key?: string | null
  timeout_seconds?: number
  max_output_tokens?: number
  top_k?: number
}

export interface AIProviderSettingsUpdatePayload {
  model?: string
  base_url?: string | null
  api_key?: string | null
  remove_api_key?: boolean
  timeout_seconds?: number
  max_output_tokens?: number
  top_k?: number
}

export interface AITestConnectionResult {
  provider: AIProvider
  model: string
  success: boolean
  latency_ms: number | null
  error_category: string | null
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatSource {
  id: string
  title: string
  url: string
  source_type: string
  snippet: string
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
  provider: string
  model: string
  request_id: string
  grounded: boolean
}

export interface ChatStatus {
  available: boolean
  provider: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
