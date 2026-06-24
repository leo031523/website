'use client'

import { useTheme } from './ThemeProvider'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return (
    <button
      onClick={toggle}
      aria-label={theme === 'dark' ? '切換淺色模式' : '切換深色模式'}
      className="text-sumi-light hover:text-sumi dark:text-dark-muted dark:hover:text-washi transition-colors text-base leading-none"
    >
      {theme === 'dark' ? '☀' : '☾'}
    </button>
  )
}
