import Link from 'next/link'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  return (
    <header className="border-b border-hairline dark:border-dark-border bg-washi dark:bg-dark-bg">
      <div className="max-w-4xl mx-auto px-6 py-5 flex items-center gap-6">
        <Link
          href="/"
          className="font-serif text-lg text-sumi dark:text-washi tracking-wide hover:text-ai dark:hover:text-dark-accent transition-colors"
        >
          Portfolio
        </Link>
        <nav className="flex gap-5 flex-1">
          <Link href="/blog" className="text-sm text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors">
            文章
          </Link>
          <Link href="/projects" className="text-sm text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors">
            作品
          </Link>
          <Link href="/about" className="text-sm text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors">
            關於
          </Link>
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href="/search"
            className="text-sm text-sumi-light dark:text-dark-muted hover:text-sumi dark:hover:text-washi transition-colors"
            aria-label="搜尋"
          >
            搜尋
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
