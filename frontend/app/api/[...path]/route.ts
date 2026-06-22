import { NextRequest, NextResponse } from 'next/server'

export const maxDuration = 60
export const dynamic = 'force-dynamic'

const BACKEND = 'https://medicalrag.duckdns.org'

async function handler(req: NextRequest) {
  const url = new URL(req.url)
  const backendUrl = `${BACKEND}${url.pathname}${url.search}`

  const headers = new Headers()
  const contentType = req.headers.get('content-type')
  if (contentType) headers.set('content-type', contentType)

  const cookie = req.headers.get('cookie')
  if (cookie) headers.set('cookie', cookie)

  let body: ArrayBuffer | undefined
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    body = await req.arrayBuffer()
  }

  const res = await fetch(backendUrl, {
    method: req.method,
    headers,
    body,
  })

  if (res.status === 204) {
    return new NextResponse(null, { status: 204 })
  }

  const resBody = await res.arrayBuffer()
  const response = new NextResponse(resBody, { status: res.status })

  res.headers.forEach((value, key) => {
    if (key.toLowerCase() === 'set-cookie') {
      response.headers.append('set-cookie', value)
    } else {
      response.headers.set(key, value)
    }
  })

  return response
}

export const GET = handler
export const POST = handler
export const PUT = handler
export const DELETE = handler
export const PATCH = handler