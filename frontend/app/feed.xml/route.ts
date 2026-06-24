import { getArticles } from '@/lib/server-api'

const SITE = process.env.SITE_URL ?? 'http://localhost'

function escape(str: string) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export async function GET() {
  const data = await getArticles({ page_size: 20 })

  const items = data.items
    .map(a => `
    <item>
      <title>${escape(a.title)}</title>
      <link>${SITE}/blog/${a.slug}</link>
      <guid isPermaLink="true">${SITE}/blog/${a.slug}</guid>
      ${a.excerpt ? `<description>${escape(a.excerpt)}</description>` : ''}
      <pubDate>${new Date(a.published_at ?? a.created_at).toUTCString()}</pubDate>
      ${a.category ? `<category>${escape(a.category.name)}</category>` : ''}
    </item>`)
    .join('')

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Portfolio</title>
    <link>${SITE}</link>
    <description>個人技術筆記與作品集</description>
    <language>zh-TW</language>
    <atom:link href="${SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    ${items}
  </channel>
</rss>`

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
