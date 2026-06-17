import type { Metadata } from 'next'
import { Noto_Sans_TC, Noto_Serif_TC } from 'next/font/google'
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
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className={`${notoSansTC.variable} ${notoSerifTC.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
