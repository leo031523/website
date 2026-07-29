import Link from 'next/link'

interface Props {
  backHref?: string
  backLabel?: string
}

export default function EndOfPage({ backHref, backLabel }: Props) {
  return (
    <div className="mt-16 pt-8 border-t border-hairline dark:border-dark-border flex flex-col items-center gap-4">
      <p className="text-xs text-sumi-light dark:text-dark-muted tracking-widest">— 到底了 —</p>
      <div className="flex items-center gap-4">
        {backHref && backLabel && (
          <Link
            href={backHref}
            className="text-sm text-sumi-light dark:text-dark-muted hover:text-ai dark:hover:text-dark-accent transition-colors"
          >
            {backLabel}
          </Link>
        )}
        <Link
          href="/"
          className="text-sm text-sumi-light dark:text-dark-muted border border-hairline dark:border-dark-border rounded-full px-5 py-2 hover:border-ai dark:hover:border-dark-accent hover:text-ai dark:hover:text-dark-accent transition-colors"
        >
          回首頁
        </Link>
      </div>
    </div>
  )
}
