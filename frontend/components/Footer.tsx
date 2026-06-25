export default function Footer() {
  return (
    <footer className="border-t border-hairline dark:border-dark-border mt-24">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <p className="text-xs text-sumi-light dark:text-dark-muted">
          © {new Date().getFullYear()} Portfolio
        </p>
      </div>
    </footer>
  )
}
