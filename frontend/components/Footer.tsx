import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="border-t border-hairline dark:border-dark-border mt-24">
      <div className="max-w-4xl mx-auto px-6 py-8 flex items-center justify-between">
        <p className="text-xs text-sumi-light dark:text-dark-muted">
          © {new Date().getFullYear()} Portfolio
        </p>
        <Link
          href="/admin/login"
          className="text-xs text-hairline dark:text-dark-border hover:text-sumi-light dark:hover:text-dark-muted transition-colors"
        >
          後台
        </Link>
      </div>
    </footer>
  )
}
