import type { Metadata } from 'next'
import { Noto_Sans_TC, Noto_Serif_TC } from 'next/font/google'
import { ThemeProvider } from '@/components/ThemeProvider'
import './globals.css'

const notoSansTC = Noto_Sans_TC({
  subsets: ['latin'],
  variable: '--font-sans',
  weight: ['300', '400', '500'],
})

const notoSerifTC = Noto_Serif_TC({
  subsets: ['latin'],
  variable: '--font-serif',
  weight: ['300', '400', '600'],
})

export const metadata: Metadata = {
  title: 'Portfolio',
  description: '個人筆記與作品集',
  alternates: {
    types: {
      'application/rss+xml': `${process.env.SITE_URL ?? 'http://localhost'}/feed.xml`,
    },
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        {/* 防止深色模式閃爍（在 hydration 前套用） */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('theme');if(!t)t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.classList.toggle('dark',t==='dark');})();`,
          }}
        />
      </head>
      <body className={`${notoSansTC.variable} ${notoSerifTC.variable} font-sans antialiased`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
