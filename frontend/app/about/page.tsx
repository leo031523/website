import type { Metadata } from 'next'
import Footer from '@/components/Footer'
import Header from '@/components/Header'

export const metadata: Metadata = {
  title: '關於 — Portfolio',
  description: '關於這個網站與作者。',
}

export default function AboutPage() {
  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="font-serif text-3xl text-sumi dark:text-washi mb-12 tracking-wide">關於</h1>
        <div className="prose prose-lg max-w-none dark:prose-invert">
          <p>
            這是一個個人筆記與作品集網站，記錄學習過的技術、使用過的工具，以及開發過的專案。
          </p>
          <p>
            網站本身就是一件作品——前後端分離、SSG/ISR、後台 CMS、Docker 部署，
            每一個環節都是可評估的工程展示。
          </p>
        </div>
      </main>
      <Footer />
    </>
  )
}
