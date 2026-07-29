import type { Metadata } from 'next'
import EndOfPage from '@/components/EndOfPage'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import ProjectCard from '@/components/ProjectCard'
import { getProjects } from '@/lib/server-api'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: '作品集 — Portfolio',
  description: '個人專案與作品展示。',
}

export default async function ProjectsPage() {
  const projects = await getProjects()
  const featured = projects.filter(p => p.featured)
  const rest = projects.filter(p => !p.featured)

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="font-serif text-3xl text-sumi dark:text-washi mb-12 tracking-wide">作品集</h1>

        {projects.length === 0 ? (
          <p className="text-sumi-light dark:text-dark-muted text-sm">尚無作品。</p>
        ) : (
          <div className="flex flex-col gap-16">
            {featured.length > 0 && (
              <section>
                <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em] mb-6">精選</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {featured.map(p => <ProjectCard key={p.id} project={p} />)}
                </div>
              </section>
            )}

            {rest.length > 0 && (
              <section>
                {featured.length > 0 && (
                  <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-[0.2em] mb-6">其他</p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {rest.map(p => <ProjectCard key={p.id} project={p} />)}
                </div>
              </section>
            )}
          </div>
        )}
        <EndOfPage />
      </main>
      <Footer />
    </>
  )
}
