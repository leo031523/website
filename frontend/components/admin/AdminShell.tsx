'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

import { api } from '@/lib/api'

interface Props {
  children: React.ReactNode
  title?: string
}

export default function AdminShell({ children, title }: Props) {
  const router = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    api.getMe()
      .then(() => setReady(true))
      .catch(() => router.replace('/admin/login'))
  }, [router])

  if (!ready) {
    return (
      <div className="min-h-screen bg-washi flex items-center justify-center">
        <p className="text-sumi-light text-sm tracking-wide">Loading…</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-washi flex">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="px-10 py-8 max-w-5xl">
          {title && (
            <h1 className="font-serif text-2xl text-sumi mb-8 tracking-wide">{title}</h1>
          )}
          {children}
        </div>
      </main>
    </div>
  )
}

function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  async function handleLogout() {
    await api.logout().catch(() => {})
    router.replace('/admin/login')
  }

  return (
    <aside className="w-48 border-r border-hairline flex-shrink-0 py-10 px-4 flex flex-col">
      <p className="text-[10px] text-sumi-light uppercase tracking-[0.2em] mb-8 px-2">
        Portfolio
      </p>
      <nav className="flex flex-col gap-0.5 flex-1">
        <NavLink href="/admin" label="儀表板" exact pathname={pathname} />
        <NavLink href="/admin/articles" label="文章管理" pathname={pathname} />
        <NavLink href="/admin/media" label="媒體庫" pathname={pathname} />
      </nav>
      <button
        onClick={handleLogout}
        className="text-left text-xs text-sumi-light hover:text-vermillion px-2 py-1.5 transition-colors"
      >
        登出
      </button>
    </aside>
  )
}

function NavLink({
  href,
  label,
  pathname,
  exact,
}: {
  href: string
  label: string
  pathname: string
  exact?: boolean
}) {
  const active = exact ? pathname === href : pathname.startsWith(href)
  return (
    <Link
      href={href}
      className={`block px-2 py-1.5 rounded text-sm transition-colors ${
        active
          ? 'text-ai font-medium bg-washi-card'
          : 'text-sumi-light hover:text-sumi hover:bg-washi-card'
      }`}
    >
      {label}
    </Link>
  )
}
