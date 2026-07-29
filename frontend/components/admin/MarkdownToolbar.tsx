'use client'

import type { RefObject } from 'react'

interface Props {
  textareaRef: RefObject<HTMLTextAreaElement | null>
  value: string
  onChange: (value: string) => void
}

const INDENT = '　　' // 全形空白 x2，中文段落慣用的視覺縮排

function getLineRange(text: string, start: number, end: number) {
  const lineStart = text.lastIndexOf('\n', start - 1) + 1
  let lineEnd = text.indexOf('\n', end)
  if (lineEnd === -1) lineEnd = text.length
  return { lineStart, lineEnd }
}

function ToolbarButton({
  label, title, onClick, className = '',
}: { label: string; title: string; onClick: () => void; className?: string }) {
  return (
    <button
      type="button"
      title={title}
      onMouseDown={e => e.preventDefault()}
      onClick={onClick}
      className={`min-w-[1.75rem] h-7 px-1.5 flex items-center justify-center text-xs text-sumi-light hover:text-sumi hover:bg-white rounded transition-colors ${className}`}
    >
      {label}
    </button>
  )
}

function Divider() {
  return <span className="w-px h-5 bg-hairline mx-1" />
}

export default function MarkdownToolbar({ textareaRef, value, onChange }: Props) {
  function replace(newText: string, selStart: number, selEnd: number) {
    onChange(newText)
    requestAnimationFrame(() => {
      const ta = textareaRef.current
      if (!ta) return
      ta.focus()
      ta.setSelectionRange(selStart, selEnd)
    })
  }

  function wrapSelection(marker: string, placeholder: string) {
    const ta = textareaRef.current
    if (!ta) return
    const start = ta.selectionStart
    const end = ta.selectionEnd
    const selected = value.slice(start, end) || placeholder
    const newText = value.slice(0, start) + marker + selected + marker + value.slice(end)
    replace(newText, start + marker.length, start + marker.length + selected.length)
  }

  function setHeading(level: 0 | 1 | 2 | 3) {
    const ta = textareaRef.current
    if (!ta) return
    const { lineStart, lineEnd } = getLineRange(value, ta.selectionStart, ta.selectionEnd)
    const stripped = value.slice(lineStart, lineEnd).replace(/^#{1,6}\s+/, '')
    const newLine = (level > 0 ? '#'.repeat(level) + ' ' : '') + stripped
    const newText = value.slice(0, lineStart) + newLine + value.slice(lineEnd)
    replace(newText, lineStart, lineStart + newLine.length)
  }

  function toggleLinePrefix(prefix: string) {
    const ta = textareaRef.current
    if (!ta) return
    const { lineStart, lineEnd } = getLineRange(value, ta.selectionStart, ta.selectionEnd)
    const lines = value.slice(lineStart, lineEnd).split('\n')
    const allPrefixed = lines.every(l => l.trim() === '' || l.startsWith(prefix))
    const newLines = lines.map(l => {
      if (l.trim() === '') return l
      return allPrefixed ? l.slice(prefix.length) : prefix + l
    })
    const newBlock = newLines.join('\n')
    const newText = value.slice(0, lineStart) + newBlock + value.slice(lineEnd)
    replace(newText, lineStart, lineStart + newBlock.length)
  }

  function insertOrderedList() {
    const ta = textareaRef.current
    if (!ta) return
    const { lineStart, lineEnd } = getLineRange(value, ta.selectionStart, ta.selectionEnd)
    const lines = value.slice(lineStart, lineEnd).split('\n')
    let n = 0
    const newLines = lines.map(l => {
      if (l.trim() === '') return l
      n += 1
      return `${n}. ${l}`
    })
    const newBlock = newLines.join('\n')
    const newText = value.slice(0, lineStart) + newBlock + value.slice(lineEnd)
    replace(newText, lineStart, lineStart + newBlock.length)
  }

  function changeIndent(add: boolean) {
    const ta = textareaRef.current
    if (!ta) return
    const { lineStart, lineEnd } = getLineRange(value, ta.selectionStart, ta.selectionEnd)
    const lines = value.slice(lineStart, lineEnd).split('\n')
    const newLines = lines.map(l => {
      if (l.trim() === '') return l
      if (add) return INDENT + l
      return l.startsWith(INDENT) ? l.slice(INDENT.length) : l.replace(/^　+/, '')
    })
    const newBlock = newLines.join('\n')
    const newText = value.slice(0, lineStart) + newBlock + value.slice(lineEnd)
    replace(newText, lineStart, lineStart + newBlock.length)
  }

  function insertLink() {
    const ta = textareaRef.current
    if (!ta) return
    const start = ta.selectionStart
    const end = ta.selectionEnd
    const selected = value.slice(start, end) || '連結文字'
    const insertion = `[${selected}](https://)`
    const newText = value.slice(0, start) + insertion + value.slice(end)
    const urlStart = start + selected.length + 3
    replace(newText, urlStart, urlStart + 'https://'.length)
  }

  function insertHr() {
    const ta = textareaRef.current
    if (!ta) return
    const pos = ta.selectionStart
    const needsNewline = pos > 0 && value[pos - 1] !== '\n'
    const insertion = `${needsNewline ? '\n' : ''}\n---\n\n`
    const newText = value.slice(0, pos) + insertion + value.slice(pos)
    const cursor = pos + insertion.length
    replace(newText, cursor, cursor)
  }

  return (
    <div className="flex items-center gap-0.5 flex-wrap px-2 py-1.5 border-b border-hairline bg-washi-card">
      <ToolbarButton label="B" title="粗體" onClick={() => wrapSelection('**', '粗體文字')} className="font-bold" />
      <ToolbarButton label="I" title="斜體" onClick={() => wrapSelection('*', '斜體文字')} className="italic" />
      <Divider />
      <ToolbarButton label="H1" title="大標題" onClick={() => setHeading(1)} />
      <ToolbarButton label="H2" title="中標題" onClick={() => setHeading(2)} />
      <ToolbarButton label="H3" title="小標題" onClick={() => setHeading(3)} />
      <ToolbarButton label="內文" title="取消標題（還原一般大小）" onClick={() => setHeading(0)} />
      <Divider />
      <ToolbarButton label="縮排+" title="增加段落縮排" onClick={() => changeIndent(true)} />
      <ToolbarButton label="縮排−" title="減少段落縮排" onClick={() => changeIndent(false)} />
      <Divider />
      <ToolbarButton label="❝" title="引用" onClick={() => toggleLinePrefix('> ')} />
      <ToolbarButton label="•" title="項目符號清單" onClick={() => toggleLinePrefix('- ')} />
      <ToolbarButton label="1." title="編號清單" onClick={insertOrderedList} />
      <Divider />
      <ToolbarButton label="</>" title="程式碼" onClick={() => wrapSelection('`', '程式碼')} />
      <ToolbarButton label="🔗" title="連結" onClick={insertLink} />
      <ToolbarButton label="—" title="分隔線" onClick={insertHr} />
    </div>
  )
}
