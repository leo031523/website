import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('access_token')?.value

  // Already on login page
  if (pathname === '/admin/login') {
    if (token) return NextResponse.redirect(new URL('/admin', request.url))
    return NextResponse.next()
  }

  // Protected admin routes
  if (!token) {
    return NextResponse.redirect(new URL('/admin/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*'],
}
