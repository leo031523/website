export default function Footer() {
  return (
    <footer className="border-t border-hairline mt-24">
      <div className="max-w-2xl mx-auto px-6 py-8">
        <p className="text-xs text-sumi-light">
          © {new Date().getFullYear()} Portfolio
        </p>
      </div>
    </footer>
  )
}
