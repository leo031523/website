import { revalidatePath, revalidateTag } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { slug, secret, type } = await request.json()

  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ message: 'Invalid secret' }, { status: 401 })
  }

  if (type === 'project') {
    revalidateTag('projects')
    revalidateTag(`project-${slug}`)
    revalidatePath('/')
    revalidatePath('/projects')
    if (slug) revalidatePath(`/projects/${slug}`)
  } else if (type === 'about') {
    revalidateTag('about')
    revalidatePath('/about')
  } else {
    revalidateTag('articles')
    revalidateTag(`article-${slug}`)
    revalidatePath('/')
    revalidatePath('/blog')
    if (slug) revalidatePath(`/blog/${slug}`)
  }

  return NextResponse.json({ revalidated: true, slug, type })
}
