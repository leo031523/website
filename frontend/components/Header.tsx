import Link from 'next/link'

export default function Header() {
  return (
    <header className="border-b border-hairline">
      <div className="max-w-4xl mx-auto px-6 py-5 flex items-center justify-between">
        <Link href="/" className="font-serif text-lg text-sumi tracking-wide hover:text-ai transition-colors">
          Portfolio
        </Link>
        <nav className="flex gap-6">
          <Link href="/blog" className="text-sm text-sumi-light hover:text-sumi transition-colors">
            文章
          </Link>
          <Link href="/projects" className="text-sm text-sumi-light hover:text-sumi transition-colors">
            作品
          </Link>
          <Link href="/about" className="text-sm text-sumi-light hover:text-sumi transition-colors">
            關於
          </Link>
        </nav>
      </div>
    </header>
  )
}
