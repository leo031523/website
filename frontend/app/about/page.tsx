import type { Metadata } from 'next'
import EndOfPage from '@/components/EndOfPage'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import { getAbout } from '@/lib/server-api'

// 沒有動態路由參數的靜態頁面，Next.js 預設會在 build 時就嘗試
// 產生靜態頁——但 docker build 階段的前端容器連不到 backend，
// 屆時 fetch 會失敗、內容被錯誤地烤進靜態 HTML。改成跟 /blog、
// /projects 列表頁一樣，每次請求時才向後端拿最新內容。
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: '關於 — Portfolio',
  description: '關於這個網站與作者。',
}

export default async function AboutPage() {
  const about = await getAbout()

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="font-serif text-3xl text-sumi dark:text-washi mb-12 tracking-wide">關於</h1>
        {about ? (
          <MarkdownRenderer content={about.content_md} />
        ) : (
          <p className="text-sumi-light dark:text-dark-muted text-sm">內容準備中。</p>
        )}
        <EndOfPage />
      </main>
      <Footer />
    </>
  )
}
