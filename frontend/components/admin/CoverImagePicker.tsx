'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'
import type { MediaItem } from '@/lib/types'

interface Props {
  imageId: number | null
  imageUrl: string | null
  onChange: (imageId: number | null, imageUrl: string | null) => void
}

function MediaLibraryModal({
  onSelect,
  onClose,
}: {
  onSelect: (item: MediaItem) => void
  onClose: () => void
}) {
  const [items, setItems] = useState<MediaItem[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.listMedia().then(setItems).finally(() => setLoading(false))
  }, [])

  async function handleUpload(files: FileList | null) {
    const file = files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const media = await api.uploadMedia(file)
      onSelect(media)
    } catch (e) {
      alert(e instanceof Error ? e.message : '上傳失敗')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-6" onClick={onClose}>
      <div
        className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-hairline">
          <h3 className="text-sm text-sumi">選擇封面圖片</h3>
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              className="hidden"
              onChange={e => handleUpload(e.target.files)}
            />
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="text-xs border border-hairline px-3 py-1.5 rounded text-sumi hover:bg-washi-card transition-colors disabled:opacity-50"
            >
              {uploading ? '上傳中…' : '+ 上傳新圖片'}
            </button>
            <button type="button" onClick={onClose} className="text-sumi-light hover:text-sumi text-sm">
              ✕
            </button>
          </div>
        </div>
        <div className="p-5 overflow-auto">
          {loading ? (
            <p className="text-sm text-sumi-light">載入中…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-sumi-light">媒體庫尚無圖片，請先上傳。</p>
          ) : (
            <div className="grid grid-cols-4 gap-3">
              {items.map(item => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelect(item)}
                  className="aspect-square rounded overflow-hidden border border-hairline hover:border-ai transition-colors"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.url} alt={item.alt_text ?? item.filename} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function CoverImagePicker({ imageId, imageUrl, onChange }: Props) {
  const [modalOpen, setModalOpen] = useState(false)

  function handleSelect(item: MediaItem) {
    onChange(item.id, item.url)
    setModalOpen(false)
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-sumi-light tracking-wide">封面圖片</label>
      <div
        onClick={() => setModalOpen(true)}
        className="relative aspect-video w-full max-w-sm border border-dashed border-hairline rounded overflow-hidden cursor-pointer hover:border-ai transition-colors bg-washi-card flex items-center justify-center"
      >
        {imageId && imageUrl ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt="封面預覽" className="w-full h-full object-cover" />
            <button
              type="button"
              onClick={e => { e.stopPropagation(); onChange(null, null) }}
              className="absolute top-2 right-2 text-xs px-2 py-1 bg-black/60 text-white rounded hover:bg-black/80 transition-colors"
            >
              移除
            </button>
          </>
        ) : (
          <p className="text-xs text-sumi-light">點擊選擇或上傳圖片</p>
        )}
      </div>

      {modalOpen && (
        <MediaLibraryModal onSelect={handleSelect} onClose={() => setModalOpen(false)} />
      )}
    </div>
  )
}
