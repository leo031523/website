import type { Metadata } from 'next'
import Link from 'next/link'
import ArticleCard from '@/components/ArticleCard'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import ProjectCard from '@/components/ProjectCard'
import { getArticles, getProjects } from '@/lib/server-api'

export const metadata: Metadata = {
  title: 'Portfolio — 筆記與作品集',
  description: '記錄技術學習的過程、工具的使用心得，以及個人專案。',
}

export default async function HomePage() {
  const [articlesData, projects] = await Promise.all([
    getArticles({ page_size: 3 }),
    getProjects(),
  ])
  const latest = articlesData.items
  const featured = projects.filter(p => p.featured).slice(0, 4)

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

        {/* Featured projects */}
        {featured.length > 0 && (
          <section className="max-w-4xl mx-auto px-6 pb-20">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em]">精選作品</h2>
              <Link href="/projects" className="text-xs text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors">
                查看全部 →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {featured.map(p => <ProjectCard key={p.id} project={p} />)}
            </div>
          </section>
        )}

        {/* Latest articles */}
        {latest.length > 0 && (
          <section className="max-w-4xl mx-auto px-6 pb-24">
            <div className="flex items-center justify-between mb-10">
              <h2 className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em]">最近文章</h2>
              <Link href="/blog" className="text-xs text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors">
                查看全部 →
              </Link>
            </div>
            <div className="flex flex-col divide-y divide-hairline dark:divide-dark-border">
              {latest.map(a => (
                <div key={a.id} className="py-8 first:pt-0 last:pb-0">
                  <ArticleCard article={a} />
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
      <Footer />
    </>
  )
}
