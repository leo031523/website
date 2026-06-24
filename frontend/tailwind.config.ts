import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 日式簡約色票（淺色）
        washi: '#FAF8F3',
        'washi-card': '#F2EFE8',
        sumi: '#1F1F1D',
        'sumi-light': '#6E6A63',
        ai: '#2E4057',
        vermillion: '#B7410E',
        hairline: '#E3DFD6',
        // 深色模式
        'dark-bg': '#1C1B19',
        'dark-card': '#252420',
        'dark-border': '#35332D',
        'dark-muted': '#9E9B94',
        'dark-accent': '#7BA7C4',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui'],
        serif: ['var(--font-serif)', 'ui-serif', 'Georgia'],
      },
      lineHeight: { reading: '1.8' },
      letterSpacing: { reading: '0.02em' },
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-body': '#1F1F1D',
            '--tw-prose-headings': '#1F1F1D',
            '--tw-prose-lead': '#6E6A63',
            '--tw-prose-links': '#2E4057',
            '--tw-prose-bold': '#1F1F1D',
            '--tw-prose-counters': '#6E6A63',
            '--tw-prose-bullets': '#E3DFD6',
            '--tw-prose-hr': '#E3DFD6',
            '--tw-prose-quotes': '#1F1F1D',
            '--tw-prose-quote-borders': '#E3DFD6',
            '--tw-prose-captions': '#6E6A63',
            '--tw-prose-code': '#1F1F1D',
            '--tw-prose-pre-code': '#1F1F1D',
            '--tw-prose-pre-bg': '#F2EFE8',
            '--tw-prose-th-borders': '#E3DFD6',
            '--tw-prose-td-borders': '#E3DFD6',
            maxWidth: 'none',
            lineHeight: '1.8',
            letterSpacing: '0.01em',
            fontFamily: 'var(--font-sans)',
            h1: { fontFamily: 'var(--font-serif)', fontWeight: '600' },
            h2: { fontFamily: 'var(--font-serif)', fontWeight: '600' },
            h3: { fontFamily: 'var(--font-serif)', fontWeight: '600' },
            a: { textDecorationThickness: '1px', textUnderlineOffset: '3px' },
            code: {
              backgroundColor: '#F2EFE8',
              padding: '0.15em 0.4em',
              borderRadius: '3px',
              fontWeight: '400',
            },
            'code::before': { content: '""' },
            'code::after': { content: '""' },
            pre: {
              backgroundColor: '#F2EFE8',
              border: '1px solid #E3DFD6',
              borderRadius: '4px',
            },
            'pre code': { backgroundColor: 'transparent', padding: '0' },
          },
        },
        invert: {
          css: {
            '--tw-prose-pre-bg': '#252420',
            pre: { backgroundColor: '#252420', border: '1px solid #35332D' },
            code: { backgroundColor: '#252420' },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

export default config
