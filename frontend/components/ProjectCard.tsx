'use client'

import Link from 'next/link'
import type { Project } from '@/lib/types'

interface Props {
  project: Project
}

export default function ProjectCard({ project }: Props) {
  return (
    <article className="group flex flex-col h-full border border-hairline dark:border-dark-border rounded-lg overflow-hidden bg-white dark:bg-dark-card hover:border-ai dark:hover:border-dark-accent transition-colors">
      <Link href={`/projects/${project.slug}`} className="flex flex-col flex-1">
        {/* Cover placeholder */}
        <div className="aspect-video bg-washi-card dark:bg-dark-bg border-b border-hairline dark:border-dark-border">
          {project.cover_image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={project.cover_image_url}
              alt={project.title}
              className="w-full h-full object-cover"
            />
          )}
        </div>

        <div className="p-5 flex flex-col flex-1">
          <h2 className="font-serif text-lg text-sumi dark:text-washi group-hover:text-ai dark:group-hover:text-dark-accent transition-colors mb-2 leading-snug">
            {project.title}
          </h2>
          {project.summary && (
            <p className="text-sm text-sumi-light dark:text-dark-muted leading-relaxed line-clamp-2">
              {project.summary}
            </p>
          )}
        </div>
      </Link>

      {/* Tech stack */}
      {project.tech_stack.length > 0 && (
        <div className="px-5 flex flex-wrap gap-1.5">
          {project.tech_stack.map(tech => (
            <span
              key={tech}
              className="text-[10px] px-2 py-0.5 bg-washi-card dark:bg-dark-bg text-sumi-light dark:text-dark-muted rounded-full"
            >
              {tech}
            </span>
          ))}
        </div>
      )}

      {/* Links */}
      {(project.repo_url || project.demo_url) && (
        <div className="px-5 py-4 flex gap-4">
          {project.repo_url && (
            <a
              href={project.repo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
              onClick={e => e.stopPropagation()}
            >
              Source →
            </a>
          )}
          {project.demo_url && (
            <a
              href={project.demo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-ai dark:text-dark-accent hover:underline"
              onClick={e => e.stopPropagation()}
            >
              Demo →
            </a>
          )}
        </div>
      )}
    </article>
  )
}
