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

function MediaCard({
  item,
  copiedId,
  onCopy,
  onDelete,
  onRename,
}: {
  item: MediaItem
  copiedId: number | null
  onCopy: (item: MediaItem) => void
  onDelete: (id: number) => void
  onRename: (id: number, name: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(item.alt_text ?? '')

  function startEdit() {
    setDraft(item.alt_text ?? '')
    setEditing(true)
  }

  function commitEdit() {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed !== (item.alt_text ?? '')) {
      onRename(item.id, trimmed)
    }
  }

  return (
    <div className="group border border-hairline rounded overflow-hidden bg-white">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={item.url}
        alt={item.alt_text ?? item.filename}
        className="w-full aspect-square object-cover"
      />
      <div className="p-2">
        {editing ? (
          <input
            autoFocus
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={e => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(false) }}
            className="text-xs text-sumi w-full border-b border-ai outline-none mb-1 bg-transparent"
          />
        ) : (
          <p
            className="text-xs text-sumi truncate mb-1 cursor-pointer hover:text-ai"
            title="點擊改名"
            onClick={startEdit}
          >
            {item.alt_text || item.filename}
          </p>
        )}
        <p className="text-[10px] text-sumi-light">{formatBytes(item.size)}</p>
        <div className="flex gap-2 mt-2">
          <button onClick={() => onCopy(item)} className="text-[10px] text-ai hover:underline">
            {copiedId === item.id ? '已複製！' : '複製 URL'}
          </button>
          <button onClick={() => onDelete(item.id)} className="text-[10px] text-sumi-light hover:text-vermillion ml-auto">
            刪除
          </button>
        </div>
      </div>
    </div>
  )
}

export default function MediaLibrary() {
  const [items, setItems] = useState<MediaItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
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
      {/* Upload zone */}
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
            <p className="text-xs text-hairline">支援 JPG、PNG、GIF、WebP，最大 10 MB｜點擊名稱可改名</p>
          </>
        )}
      </div>

      {/* Grid */}
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
            />
          ))}
        </div>
      )}
    </AdminShell>
  )
}
