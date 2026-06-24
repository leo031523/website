import { revalidatePath, revalidateTag } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { slug, secret } = await request.json()

  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ message: 'Invalid secret' }, { status: 401 })
  }

  revalidateTag('articles')
  revalidateTag(`article-${slug}`)
  revalidatePath('/')
  revalidatePath('/blog')
  if (slug) revalidatePath(`/blog/${slug}`)

  return NextResponse.json({ revalidated: true, slug })
}
