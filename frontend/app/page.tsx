import type { Metadata } from 'next'
import Link from 'next/link'
import Footer from '@/components/Footer'
import Header from '@/components/Header'

export const metadata: Metadata = {
  title: 'Portfolio — 筆記與作品集',
  description: '記錄技術學習的過程、工具的使用心得，以及個人專案。',
}

const TECH_STACK = [
  {
    category: '前端',
    items: ['Next.js 15 (App Router)', 'TypeScript', 'Tailwind CSS'],
  },
  {
    category: '後端',
    items: ['FastAPI', 'SQLAlchemy', 'Alembic'],
  },
  {
    category: '資料庫',
    items: ['PostgreSQL 16'],
  },
  {
    category: '部署',
    items: ['Docker Compose', 'nginx', "Let's Encrypt / Certbot"],
  },
  {
    category: 'CI/CD',
    items: ['GitHub Actions'],
  },
]

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        {/* Hero */}
        <section className="max-w-4xl mx-auto px-6 py-16">
          <h1 className="font-serif text-3xl text-sumi dark:text-washi leading-tight mb-6 tracking-wide">
            筆記與作品集
          </h1>
          <p className="text-sumi-light dark:text-dark-muted leading-relaxed max-w-md">
            記錄使用過的工具、技術心得與學習筆記，並陳列個人專案與作品。
          </p>
          <div className="flex gap-6 mt-8">
            <Link href="/blog" className="text-sm text-ai dark:text-dark-accent border-b border-ai dark:border-dark-accent pb-0.5 hover:text-sumi dark:hover:text-washi hover:border-sumi dark:hover:border-washi transition-colors">
              閱讀文章
            </Link>
            <Link href="/projects" className="text-sm text-sumi-light dark:text-dark-muted border-b border-hairline dark:border-dark-border pb-0.5 hover:text-sumi dark:hover:text-washi transition-colors">
              查看作品
            </Link>
            <Link href="/about" className="text-sm text-sumi-light dark:text-dark-muted border-b border-hairline dark:border-dark-border pb-0.5 hover:text-sumi dark:hover:text-washi transition-colors">
              關於我
            </Link>
          </div>
        </section>

        {/* Tech stack */}
        <section className="max-w-4xl mx-auto px-6 pb-24">
          <div className="mb-10">
            <h2 className="text-sm text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em]">技術棧</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-10">
            {TECH_STACK.map(group => (
              <div key={group.category}>
                <h3 className="font-serif text-xl text-sumi dark:text-washi mb-4 pb-2 border-b border-hairline dark:border-dark-border">
                  {group.category}
                </h3>
                <ul className="space-y-2">
                  {group.items.map(item => (
                    <li
                      key={item}
                      className="text-sm text-sumi-light dark:text-dark-muted leading-relaxed"
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
