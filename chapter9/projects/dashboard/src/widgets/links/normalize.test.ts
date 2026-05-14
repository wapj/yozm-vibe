import { describe, it, expect } from 'vitest'
import { normalizeUrl } from './normalize'

describe('normalizeUrl', () => {
  it('호스트 소문자 통일', () => {
    expect(normalizeUrl('https://EXAMPLE.com/path')).toBe('https://example.com/path')
  })

  it('스킴 소문자 통일', () => {
    expect(normalizeUrl('HTTPS://example.com/path')).toBe('https://example.com/path')
  })

  it('끝 슬래시 제거(path 있음)', () => {
    expect(normalizeUrl('https://example.com/foo/')).toBe('https://example.com/foo')
  })

  it('루트 슬래시 처리', () => {
    expect(normalizeUrl('https://example.com/')).toBe('https://example.com')
  })

  it('쿼리 보존', () => {
    expect(normalizeUrl('https://example.com/path?q=1&r=2')).toBe('https://example.com/path?q=1&r=2')
  })

  it('해시 보존', () => {
    expect(normalizeUrl('https://example.com/path#section')).toBe('https://example.com/path#section')
  })

  it('쿼리+해시+끝슬래시 조합', () => {
    expect(normalizeUrl('https://example.com/path/?q=1#x')).toBe('https://example.com/path?q=1#x')
  })

  it('공백 트림', () => {
    expect(normalizeUrl('  https://example.com/  ')).toBe('https://example.com')
  })

  it('잘못된 URL throw', () => {
    expect(() => normalizeUrl('not-a-url')).toThrow()
  })
})
