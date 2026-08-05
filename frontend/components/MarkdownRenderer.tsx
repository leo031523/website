import type { ComponentPropsWithoutRef } from 'react'
import ReactMarkdown, { type ExtraProps } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

interface Props {
  content: string
}

// 頁面本身已經有一個 <h1>（文章/作品標題），Markdown 內容裡的標題
// 一律降一級渲染，避免同一頁出現兩個 <h1>，並維持正確的
// heading hierarchy（h1 只有一個，內容從 h2 開始）。
// react-markdown 額外傳入 `node`（mdast AST 節點），只給元件自己用，
// 不應原樣轉發到真正的 DOM 元素上，否則會變成無效的 HTML 屬性。
const headingComponents = {
  h1: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h2'> & ExtraProps) => <h2 {...rest} />,
  h2: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h3'> & ExtraProps) => <h3 {...rest} />,
  h3: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h4'> & ExtraProps) => <h4 {...rest} />,
  h4: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h5'> & ExtraProps) => <h5 {...rest} />,
  h5: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h6'> & ExtraProps) => <h6 {...rest} />,
  h6: ({ node: _node, ...rest }: ComponentPropsWithoutRef<'h6'> & ExtraProps) => <h6 {...rest} />,
}

export default function MarkdownRenderer({ content }: Props) {
  return (
    <div className="prose prose-lg max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={headingComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
