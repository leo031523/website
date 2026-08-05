'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AdminShell from '@/components/admin/AdminShell'
import CoverImagePicker from '@/components/admin/CoverImagePicker'
import MarkdownToolbar from '@/components/admin/MarkdownToolbar'
import { useToast } from '@/components/admin/Toast'
import { api } from '@/lib/api'
import type { ProjectPayload, Tag, Tool } from '@/lib/types'

function slugify(s: string) {
  return s.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').replace(/^-+|-+$/g, '') || ''
}

export default function ProjectEditor() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const router = useRouter()
  const toast = useToast()

  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [slugManual, setSlugManual] = useState(false)
  const [summary, setSummary] = useState('')
  const [content, setContent] = useState('')
  const [techInput, setTechInput] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [demoUrl, setDemoUrl] = useState('')
  const [status, setStatus] = useState<'draft' | 'published'>('draft')
  const [featured, setFeatured] = useState(false)
  const [sortOrder, setSortOrder] = useState(0)
  const [coverImageId, setCoverImageId] = useState<number | null>(null)
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [selectedToolIds, setSelectedToolIds] = useState<number[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const contentRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!slugManual) setSlug(slugify(title))
  }, [title, slugManual])

  useEffect(() => {
    Promise.all([api.listTags(), api.listTools()]).then(([t, to]) => {
      setTags(t); setTools(to)
    })
    if (!isNew) {
      api.getProjectById(Number(id)).then(p => {
        setTitle(p.title); setSlug(p.slug); setSlugManual(true)
        setSummary(p.summary ?? ''); setContent(p.content_md ?? '')
        setTechInput(p.tech_stack.join(', '))
        setRepoUrl(p.repo_url ?? ''); setDemoUrl(p.demo_url ?? '')
        setStatus(p.status); setFeatured(p.featured); setSortOrder(p.sort_order)
        setCoverImageId(p.cover_image_id); setCoverImageUrl(p.cover_image_url)
        setSelectedTagIds(p.tags.map(t => t.id))
        setSelectedToolIds(p.tools.map(t => t.id))
      }).catch(() => router.replace('/admin/projects'))
    }
  }, [id, isNew, router])

  function normalizeUrl(value: string): string {
    const trimmed = value.trim()
    if (!trimmed) return ''
    if (/^https?:\/\//i.test(trimmed)) return trimmed
    return `https://${trimmed}`
  }

  async function save(targetStatus: 'draft' | 'published') {
    if (!title.trim()) { setError('請填寫標題'); return }
    setError(''); setSaving(true)
    const techStack = techInput.split(',').map(s => s.trim()).filter(Boolean)
    const payload: ProjectPayload = {
      title, slug: slug || undefined, summary: summary || null,
      content_md: content, tech_stack: techStack,
      repo_url: repoUrl ? normalizeUrl(repoUrl) : null,
      demo_url: demoUrl ? normalizeUrl(demoUrl) : null,
      status: targetStatus, featured, sort_order: sortOrder,
      tag_ids: selectedTagIds, tool_ids: selectedToolIds,
      cover_image_id: coverImageId,
    }
    try {
      const result = isNew
        ? await api.createProject(payload)
        : await api.updateProject(Number(id), payload)
      toast.success(targetStatus === 'published' ? '作品已發布' : '草稿已儲存')
      if (isNew) router.replace(`/admin/projects/${result.id}`)
    } catch (e) {
      const message = e instanceof Error ? e.message : '儲存失敗'
      setError(message)
      toast.error(message)
    } finally { setSaving(false) }
  }

  return (
    <AdminShell>
      <div className="flex flex-col gap-6 max-w-6xl">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/admin/projects" className="text-sumi-light hover:text-sumi text-sm transition-colors">
            ← 作品列表
          </Link>
          <span className="text-hairline">|</span>
          <span className="text-xs text-sumi-light">{isNew ? '新增作品' : '編輯作品'}</span>
          <div className="ml-auto flex items-center gap-3">
            {error && (
              <span id="project-form-error" role="alert" className="text-xs text-vermillion">
                {error}
              </span>
            )}
            <button onClick={() => save('draft')} disabled={saving}
              className="text-sm border border-hairline px-4 py-1.5 rounded text-sumi hover:bg-washi-card transition-colors disabled:opacity-50">
              {saving ? '儲存中…' : '儲存草稿'}
            </button>
            <button onClick={() => save('published')} disabled={saving}
              className="text-sm bg-ai text-washi px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50">
              {saving ? '發布中…' : '發布'}
            </button>
          </div>
        </div>

        {/* Title */}
        <label htmlFor="project-title" className="sr-only">作品標題</label>
        <input
          id="project-title" name="title"
          type="text" placeholder="作品標題" value={title} onChange={e => setTitle(e.target.value)}
          aria-describedby={error ? 'project-form-error' : undefined}
          aria-invalid={error ? true : undefined}
          className="font-serif text-2xl text-sumi border-0 border-b border-hairline bg-transparent focus:outline-none focus:border-ai py-2 transition-colors placeholder:text-hairline" />

        {/* Slug */}
        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="project-slug" className="text-sumi-light">slug:</label>
          <input
            id="project-slug" name="slug"
            type="text" value={slug} onChange={e => { setSlug(e.target.value); setSlugManual(true) }}
            className="text-sumi-light border-b border-hairline bg-transparent focus:outline-none focus:border-ai py-0.5 flex-1 transition-colors" />
        </div>

        {/* Cover image */}
        <CoverImagePicker
          imageId={coverImageId}
          imageUrl={coverImageUrl}
          onChange={(id, url) => { setCoverImageId(id); setCoverImageUrl(url) }}
        />

        {/* Split editor */}
        <div className="flex flex-col border border-hairline rounded overflow-hidden">
          <MarkdownToolbar textareaRef={contentRef} value={content} onChange={setContent} />
          <div className="grid grid-cols-2 gap-0" style={{ height: '50vh' }}>
            <label htmlFor="project-content" className="sr-only">作品說明（Markdown）</label>
            <textarea
              id="project-content" name="content_md"
              ref={contentRef} value={content} onChange={e => setContent(e.target.value)}
              placeholder="以 Markdown 撰寫專案說明…"
              className="p-4 font-mono text-sm text-sumi bg-white resize-none focus:outline-none border-r border-hairline leading-relaxed" />
            <div className="p-4 overflow-auto prose prose-sm max-w-none text-sumi">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || '*預覽*'}</ReactMarkdown>
            </div>
          </div>
        </div>

        {/* Meta */}
        <div className="grid grid-cols-2 gap-6">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="project-summary" className="text-xs text-sumi-light tracking-wide">摘要</label>
            <textarea
              id="project-summary" name="summary"
              value={summary} onChange={e => setSummary(e.target.value)} rows={2}
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai resize-none" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="project-tech" className="text-xs text-sumi-light tracking-wide">技術棧（逗號分隔）</label>
            <input
              id="project-tech" name="tech_stack"
              type="text" value={techInput} onChange={e => setTechInput(e.target.value)}
              placeholder="React, TypeScript, FastAPI…"
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="project-repo-url" className="text-xs text-sumi-light tracking-wide">Source URL</label>
            <input
              id="project-repo-url" name="repo_url"
              type="url" value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              onBlur={e => setRepoUrl(normalizeUrl(e.target.value))}
              placeholder="github.com/you/project"
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="project-demo-url" className="text-xs text-sumi-light tracking-wide">Demo URL</label>
            <input
              id="project-demo-url" name="demo_url"
              type="url" value={demoUrl}
              onChange={e => setDemoUrl(e.target.value)}
              onBlur={e => setDemoUrl(normalizeUrl(e.target.value))}
              placeholder="your-demo.example.com"
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai" />
          </div>
        </div>

        {/* Options row */}
        <div className="flex items-center gap-8">
          <label htmlFor="project-featured" className="flex items-center gap-2 cursor-pointer">
            <input
              id="project-featured" name="featured"
              type="checkbox" checked={featured} onChange={e => setFeatured(e.target.checked)}
              className="accent-ai" />
            <span className="text-sm text-sumi">精選（首頁顯示）</span>
          </label>
          <div className="flex items-center gap-2">
            <label htmlFor="project-sort-order" className="text-xs text-sumi-light">排序</label>
            <input
              id="project-sort-order" name="sort_order"
              type="number" value={sortOrder} onChange={e => setSortOrder(Number(e.target.value))}
              className="w-16 border border-hairline rounded px-2 py-1 text-sm text-sumi bg-white focus:outline-none focus:border-ai" />
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-xs text-sumi-light tracking-wide">標籤</span>
            <div className="flex flex-wrap gap-2">
              {tags.map(t => (
                <button key={t.id} type="button"
                  onClick={() => setSelectedTagIds(prev => prev.includes(t.id) ? prev.filter(x => x !== t.id) : [...prev, t.id])}
                  aria-pressed={selectedTagIds.includes(t.id)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    selectedTagIds.includes(t.id) ? 'border-ai bg-ai/10 text-ai' : 'border-hairline text-sumi-light hover:border-ai'
                  }`}>
                  {t.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tools */}
        {tools.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-xs text-sumi-light tracking-wide">使用工具</span>
            <div className="flex flex-wrap gap-2">
              {tools.map(t => (
                <button key={t.id} type="button"
                  onClick={() => setSelectedToolIds(prev => prev.includes(t.id) ? prev.filter(x => x !== t.id) : [...prev, t.id])}
                  aria-pressed={selectedToolIds.includes(t.id)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    selectedToolIds.includes(t.id) ? 'border-ai bg-ai/10 text-ai' : 'border-hairline text-sumi-light hover:border-ai'
                  }`}>
                  {t.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </AdminShell>
  )
}
