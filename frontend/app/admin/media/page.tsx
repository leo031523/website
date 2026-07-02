'use client'

import { useRef, useState, useEffect } from 'react'
import AdminShell from '@/components/admin/AdminShell'
import { api } from '@/lib/api'
import type { MediaItem } from '@/lib/types'

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}

function Lightbox({ item, onClose }: { item: MediaItem; onClose: () => void }) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 bg-black/75 flex flex-col items-center justify-center p-6"
      onClick={onClose}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={item.url}
        alt={item.alt_text ?? item.filename}
        className="max-w-full max-h-[80vh] object-contain rounded shadow-lg"
        onClick={e => e.stopPropagation()}
      />
      <p className="mt-4 text-white/70 text-sm">
        {item.alt_text || item.filename} · {formatBytes(item.size)}
      </p>
      <p className="mt-1 text-white/40 text-xs">點擊外部或按 Esc 關閉</p>
    </div>
  )
}

function MediaCard({
  item,
  copiedId,
  onCopy,
  onDelete,
  onRename,
  onPreview,
}: {
  item: MediaItem
  copiedId: number | null
  onCopy: (item: MediaItem) => void
  onDelete: (id: number) => void
  onRename: (id: number, name: string) => void
  onPreview: (item: MediaItem) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(item.alt_text ?? '')
  const [menuOpen, setMenuOpen] = useState(false)

  function startEdit() {
    setDraft(item.alt_text ?? '')
    setEditing(true)
    setMenuOpen(false)
  }

  function commitEdit() {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed !== (item.alt_text ?? '')) {
      onRename(item.id, trimmed)
    }
  }

  return (
    <div className="border border-hairline rounded bg-white">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={item.url}
        alt={item.alt_text ?? item.filename}
        className="w-full aspect-square object-cover rounded-t cursor-zoom-in"
        onClick={() => onPreview(item)}
      />
      <div className="p-2">
        <div className="flex items-start gap-1 mb-1">
          {editing ? (
            <input
              autoFocus
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onBlur={commitEdit}
              onKeyDown={e => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(false) }}
              className="text-xs text-sumi flex-1 border-b border-ai outline-none bg-transparent"
            />
          ) : (
            <p className="text-xs text-sumi truncate flex-1">
              {item.alt_text || item.filename}
            </p>
          )}
          <div className="relative flex-shrink-0">
            <button
              onClick={() => setMenuOpen(o => !o)}
              className="text-sumi-light hover:text-sumi transition-colors px-0.5 leading-none text-sm"
              aria-label="選單"
            >
              ⋯
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-5 z-20 bg-white border border-hairline rounded shadow-sm py-1 w-24">
                  <button
                    onClick={startEdit}
                    className="block w-full text-left px-3 py-1.5 text-xs text-sumi hover:bg-washi-card transition-colors"
                  >
                    改名
                  </button>
                  <button
                    onClick={() => { onCopy(item); setMenuOpen(false) }}
                    className="block w-full text-left px-3 py-1.5 text-xs text-sumi hover:bg-washi-card transition-colors"
                  >
                    {copiedId === item.id ? '已複製！' : '複製 URL'}
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onDelete(item.id) }}
                    className="block w-full text-left px-3 py-1.5 text-xs text-vermillion hover:bg-washi-card transition-colors"
                  >
                    刪除
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
        <p className="text-[10px] text-sumi-light">
          {formatBytes(item.size)} · {new Date(item.created_at).toLocaleDateString('zh-TW')}
        </p>
      </div>
    </div>
  )
}

export default function MediaLibrary() {
  const [items, setItems] = useState<MediaItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [preview, setPreview] = useState<MediaItem | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.listMedia().then(setItems).finally(() => setLoading(false))
  }, [])

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return
    setUploading(true)
    try {
      const results = await Promise.all(Array.from(files).map(f => api.uploadMedia(f)))
      setItems(prev => [...results.reverse(), ...prev])
    } catch (e) {
      alert(e instanceof Error ? e.message : '上傳失敗')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('確定刪除此檔案？')) return
    await api.deleteMedia(id)
    setItems(prev => prev.filter(m => m.id !== id))
  }

  async function handleRename(id: number, name: string) {
    const updated = await api.updateMedia(id, { alt_text: name || null })
    setItems(prev => prev.map(m => m.id === id ? updated : m))
  }

  function copyUrl(item: MediaItem) {
    navigator.clipboard.writeText(item.url)
    setCopiedId(item.id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    handleFiles(e.dataTransfer.files)
  }

  return (
    <AdminShell title="媒體庫">
      {preview && <Lightbox item={preview} onClose={() => setPreview(null)} />}

      <div
        onDrop={onDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-hairline rounded-lg p-10 text-center cursor-pointer hover:border-ai transition-colors mb-8"
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          multiple
          className="hidden"
          onChange={e => handleFiles(e.target.files)}
        />
        {uploading ? (
          <p className="text-sm text-sumi-light">上傳中…</p>
        ) : (
          <>
            <p className="text-sm text-sumi-light mb-1">拖放圖片至此，或點擊選擇</p>
            <p className="text-xs text-hairline">支援 JPG、PNG、GIF、WebP，最大 10 MB</p>
          </>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-sumi-light">載入中…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-sumi-light">尚無媒體檔案</p>
      ) : (
        <div className="grid grid-cols-4 gap-4">
          {items.map(item => (
            <MediaCard
              key={item.id}
              item={item}
              copiedId={copiedId}
              onCopy={copyUrl}
              onDelete={handleDelete}
              onRename={handleRename}
              onPreview={setPreview}
            />
          ))}
        </div>
      )}
    </AdminShell>
  )
}
