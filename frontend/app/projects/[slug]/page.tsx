import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import { getProject } from '@/lib/server-api'

const SITE = process.env.SITE_URL ?? 'http://localhost'

interface Props {
  params: Promise<{ slug: string }>
}

export const dynamicParams = true
export async function generateStaticParams() { return [] }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const project = await getProject(slug)
  if (!project) return {}
  return {
    title: `${project.title} — Portfolio`,
    description: project.summary ?? undefined,
    openGraph: {
      title: project.title,
      description: project.summary ?? undefined,
      type: 'website',
      url: `${SITE}/projects/${slug}`,
    },
  }
}

export default async function ProjectPage({ params }: Props) {
  const { slug } = await params
  const project = await getProject(slug)
  if (!project) notFound()

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareSourceCode',
    name: project.title,
    description: project.summary,
    url: `${SITE}/projects/${slug}`,
    codeRepository: project.repo_url,
  }

  return (
    <>
      <Header />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <main className="max-w-4xl mx-auto px-6 py-16">
        {/* Header */}
        <h1 className="font-serif text-3xl text-sumi dark:text-washi leading-tight mb-4 tracking-wide">
          {project.title}
        </h1>
        {project.summary && (
          <p className="text-sumi-light dark:text-dark-muted leading-relaxed mb-8">{project.summary}</p>
        )}

        {/* Links */}
        {(project.repo_url || project.demo_url) && (
          <div className="flex gap-6 mb-8 pb-8 border-b border-hairline dark:border-dark-border">
            {project.repo_url && (
              <a href={project.repo_url} target="_blank" rel="noopener noreferrer"
                className="text-sm text-ai dark:text-dark-accent border-b border-ai dark:border-dark-accent pb-0.5 hover:text-sumi dark:hover:text-washi hover:border-sumi dark:hover:border-washi transition-colors">
                Source Code →
              </a>
            )}
            {project.demo_url && (
              <a href={project.demo_url} target="_blank" rel="noopener noreferrer"
                className="text-sm text-sumi-light dark:text-dark-muted border-b border-hairline dark:border-dark-border pb-0.5 hover:text-sumi dark:hover:text-washi transition-colors">
                Live Demo →
              </a>
            )}
          </div>
        )}

        {/* Tech stack */}
        {project.tech_stack.length > 0 && (
          <div className="mb-8">
            <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-widest mb-3">技術棧</p>
            <div className="flex flex-wrap gap-2">
              {project.tech_stack.map(t => (
                <span key={t} className="text-xs px-3 py-1 bg-washi-card dark:bg-dark-card text-sumi dark:text-washi rounded-full">
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Tools */}
        {project.tools.length > 0 && (
          <div className="mb-10 pb-8 border-b border-hairline dark:border-dark-border">
            <p className="text-xs text-sumi-light dark:text-dark-muted uppercase tracking-widest mb-3">使用工具</p>
            <div className="flex flex-wrap gap-2">
              {project.tools.map(t => (
                <a
                  key={t.id}
                  href={t.url ?? undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-3 py-1 border border-hairline dark:border-dark-border text-sumi-light dark:text-dark-muted rounded-full hover:border-ai dark:hover:border-dark-accent hover:text-ai dark:hover:text-dark-accent transition-colors"
                >
                  {t.name}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {project.tags.length > 0 && (
          <div className="flex gap-2 mb-10">
            {project.tags.map(t => (
              <span key={t.id} className="text-xs px-2 py-0.5 bg-washi-card dark:bg-dark-card text-sumi-light dark:text-dark-muted rounded-full">
                {t.name}
              </span>
            ))}
          </div>
        )}

        {/* Content */}
        {project.content_md && <MarkdownRenderer content={project.content_md} />}

        {/* Back */}
        <div className="mt-16 pt-8 border-t border-hairline dark:border-dark-border">
          <Link
            href="/projects"
            className="text-sm text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
          >
            ← 返回作品列表
          </Link>
        </div>
      </main>
      <Footer />
    </>
  )
}
