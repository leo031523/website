'use client'

import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AdminShell from '@/components/admin/AdminShell'
import MarkdownToolbar from '@/components/admin/MarkdownToolbar'
import { useToast } from '@/components/admin/Toast'
import { api } from '@/lib/api'

export default function AboutEditor() {
  const toast = useToast()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const contentRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    api.getAbout()
      .then(a => setContent(a.content_md))
      .catch(() => setError('載入失敗'))
      .finally(() => setLoading(false))
  }, [])

  async function save() {
    setError('')
    setSaving(true)
    try {
      await api.updateAbout(content)
      toast.success('關於我內容已儲存')
    } catch (e) {
      const message = e instanceof Error ? e.message : '儲存失敗'
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <AdminShell>
      <div className="flex flex-col gap-6 max-w-6xl">
        <div className="flex items-center gap-4">
          <span className="text-xs text-sumi-light">關於我</span>
          <div className="ml-auto flex items-center gap-3">
            {error && (
              <span id="about-form-error" role="alert" className="text-xs text-vermillion">
                {error}
              </span>
            )}
            <button
              onClick={save}
              disabled={saving || loading}
              className="text-sm bg-ai text-washi px-4 py-1.5 rounded hover:bg-sumi transition-colors disabled:opacity-50"
            >
              {saving ? '儲存中…' : '儲存'}
            </button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-sumi-light">載入中…</p>
        ) : (
          <div className="flex flex-col border border-hairline rounded overflow-hidden">
            <MarkdownToolbar textareaRef={contentRef} value={content} onChange={setContent} />
            <div className="grid grid-cols-2 gap-0" style={{ height: '60vh' }}>
              <label htmlFor="about-content" className="sr-only">關於我內容（Markdown）</label>
              <textarea
                id="about-content"
                name="content_md"
                ref={contentRef}
                value={content}
                onChange={e => setContent(e.target.value)}
                aria-describedby={error ? 'about-form-error' : undefined}
                aria-invalid={error ? true : undefined}
                placeholder="以 Markdown 撰寫關於我內容…"
                className="p-4 font-mono text-sm text-sumi bg-white resize-none focus:outline-none border-r border-hairline leading-relaxed"
              />
              <div className="p-4 overflow-auto prose prose-sm max-w-none text-sumi">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || '*預覽將顯示在此*'}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminShell>
  )
}
