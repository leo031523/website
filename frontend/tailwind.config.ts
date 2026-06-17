import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 日式簡約色票（§6.2）
        washi: '#FAF8F3',
        'washi-card': '#F2EFE8',
        sumi: '#1F1F1D',
        'sumi-light': '#6E6A63',
        ai: '#2E4057',
        vermillion: '#B7410E',
        hairline: '#E3DFD6',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui'],
        serif: ['var(--font-serif)', 'ui-serif', 'Georgia'],
      },
      lineHeight: {
        reading: '1.8',
      },
      letterSpacing: {
        reading: '0.02em',
      },
    },
  },
  plugins: [],
}

export default config
