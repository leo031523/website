'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AdminShell from '@/components/admin/AdminShell'
import CoverImagePicker from '@/components/admin/CoverImagePicker'
import { api } from '@/lib/api'
import type { ArticlePayload, Category, Tag } from '@/lib/types'

function slugify(s: string) {
  return s
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-+|-+$/g, '') || ''
}

export default function ArticleEditor() {
  const { id } = useParams<{ id: string }>()
  const isNew = id === 'new'
  const router = useRouter()

  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [slugManual, setSlugManual] = useState(false)
  const [excerpt, setExcerpt] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState<'draft' | 'published'>('draft')
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [coverImageId, setCoverImageId] = useState<number | null>(null)
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  // Auto-generate slug from title
  useEffect(() => {
    if (!slugManual) setSlug(slugify(title))
  }, [title, slugManual])

  // Load categories, tags, and article (if editing)
  useEffect(() => {
    Promise.all([api.listCategories(), api.listTags()]).then(([cats, tags]) => {
      setCategories(cats)
      setTags(tags)
    })

    if (!isNew) {
      api.getArticleById(Number(id)).then(a => {
        setTitle(a.title)
        setSlug(a.slug)
        setSlugManual(true)
        setExcerpt(a.excerpt ?? '')
        setContent(a.content_md ?? '')
        setStatus(a.status)
        setCategoryId(a.category?.id ?? null)
        setCoverImageId(a.cover_image_id)
        setCoverImageUrl(a.cover_image_url)
        setSelectedTagIds(a.tags.map(t => t.id))
      }).catch(() => router.replace('/admin/articles'))
    }
  }, [id, isNew, router])

  async function save(targetStatus: 'draft' | 'published') {
    if (!title.trim()) { setError('請填寫標題'); return }
    setError(''); setSaving(true)
    const payload: ArticlePayload = {
      title,
      slug: slug || undefined,
      excerpt: excerpt || null,
      content_md: content,
      status: targetStatus,
      category_id: categoryId,
      tag_ids: selectedTagIds,
      cover_image_id: coverImageId,
    }
    try {
      const saved = isNew
        ? await api.createArticle(payload)
        : await api.updateArticle(Number(id), payload)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      if (isNew) router.replace(`/admin/articles/${saved.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : '儲存失敗')
    } finally {
      setSaving(false)
    }
  }

  function toggleTag(tagId: number) {
    setSelectedTagIds(prev =>
      prev.includes(tagId) ? prev.filter(t => t !== tagId) : [...prev, tagId]
    )
  }

  return (
    <AdminShell>
      <div className="flex flex-col gap-6 max-w-6xl">
        {/* Header bar */}
        <div className="flex items-center gap-4">
          <Link href="/admin/articles" className="text-sumi-light hover:text-sumi text-sm transition-colors">
            ← 文章列表
          </Link>
          <span className="text-hairline">|</span>
          <span className="text-xs text-sumi-light">{isNew ? '新增文章' : '編輯文章'}</span>
          <div className="ml-auto flex items-center gap-3">
            {saved && <span className="text-xs text-ai">已儲存 ✓</span>}
            {error && <span className="text-xs text-vermillion">{error}</span>}
            <button
              onClick={() => save('draft')}
              disabled={saving}
              className="text-sm border border-hairline px-4 py-1.5 rounded text-sumi hover:bg-washi-card transition-colors disabled:opacity-50"
            >
              儲存草稿
            </button>
            <button
              onClick={() => save('published')}
              disabled={saving}
              className="text-sm bg-ai text-washi px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50"
            >
              發布
            </button>
          </div>
        </div>

        {/* Title */}
        <input
          type="text"
          placeholder="文章標題"
          value={title}
          onChange={e => setTitle(e.target.value)}
          className="font-serif text-2xl text-sumi border-0 border-b border-hairline bg-transparent focus:outline-none focus:border-ai py-2 transition-colors placeholder:text-hairline"
        />

        {/* Slug */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-sumi-light">slug:</span>
          <input
            type="text"
            value={slug}
            onChange={e => { setSlug(e.target.value); setSlugManual(true) }}
            placeholder="auto-generated"
            className="text-sumi-light border-b border-hairline bg-transparent focus:outline-none focus:border-ai py-0.5 flex-1 transition-colors"
          />
        </div>

        {/* Cover image */}
        <CoverImagePicker
          imageId={coverImageId}
          imageUrl={coverImageUrl}
          onChange={(id, url) => { setCoverImageId(id); setCoverImageUrl(url) }}
        />

        {/* Split editor */}
        <div className="grid grid-cols-2 gap-0 border border-hairline rounded overflow-hidden" style={{ height: '60vh' }}>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="以 Markdown 撰寫內容…"
            className="p-4 font-mono text-sm text-sumi bg-white resize-none focus:outline-none border-r border-hairline leading-relaxed"
          />
          <div className="p-4 overflow-auto prose prose-sm max-w-none text-sumi">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || '*預覽將顯示在此*'}</ReactMarkdown>
          </div>
        </div>

        {/* Meta row */}
        <div className="grid grid-cols-3 gap-6">
          {/* Excerpt */}
          <div className="col-span-2 flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light tracking-wide">摘要（選填）</label>
            <textarea
              value={excerpt}
              onChange={e => setExcerpt(e.target.value)}
              rows={2}
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors resize-none"
            />
          </div>

          {/* Category */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-sumi-light tracking-wide">分類</label>
            <select
              value={categoryId ?? ''}
              onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : null)}
              className="border border-hairline rounded px-3 py-2 text-sm text-sumi bg-white focus:outline-none focus:border-ai transition-colors"
            >
              <option value="">— 無分類 —</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-col gap-2">
            <label className="text-xs text-sumi-light tracking-wide">標籤</label>
            <div className="flex flex-wrap gap-2">
              {tags.map(t => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => toggleTag(t.id)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    selectedTagIds.includes(t.id)
                      ? 'border-ai bg-ai/10 text-ai'
                      : 'border-hairline text-sumi-light hover:border-ai hover:text-sumi'
                  }`}
                >
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
