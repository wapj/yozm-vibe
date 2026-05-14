export function normalizeUrl(input: string): string {
  const trimmed = input.trim()
  const url = new URL(trimmed)
  const scheme = url.protocol.toLowerCase()
  const host = url.host.toLowerCase()
  let path = url.pathname
  if (path === '/') {
    path = ''
  } else {
    path = path.replace(/\/+$/, '')
  }
  return `${scheme}//${host}${path}${url.search}${url.hash}`
}
