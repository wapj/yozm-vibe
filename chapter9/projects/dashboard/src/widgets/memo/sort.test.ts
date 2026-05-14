import { describe, it, expect } from 'vitest'
import { sortMemos } from './sort'
import type { MemoItem } from './types'

function item(id: string, createdAt: number, done = false): MemoItem {
  return { id, text: id, done, createdAt }
}

describe('sortMemos', () => {
  it('빈 배열', () => {
    expect(sortMemos([])).toEqual([])
  })

  it('모두 미완료 — createdAt 내림차순', () => {
    const input = [item('a', 100), item('b', 300), item('c', 200)]
    const result = sortMemos(input)
    expect(result.map(i => i.createdAt)).toEqual([300, 200, 100])
  })

  it('모두 완료 — createdAt 내림차순', () => {
    const input = [item('a', 100, true), item('b', 300, true), item('c', 200, true)]
    const result = sortMemos(input)
    expect(result.map(i => i.createdAt)).toEqual([300, 200, 100])
  })

  it('혼합 — 미완료 그룹 앞, 완료 그룹 뒤, 각 그룹 내 createdAt 내림차순', () => {
    const input = [
      item('a', 100, false),
      item('b', 200, true),
      item('c', 300, false),
      item('d', 400, true),
    ]
    const result = sortMemos(input)
    expect(result.map(i => i.createdAt)).toEqual([300, 100, 400, 200])
    expect(result.slice(0, 2).every(i => !i.done)).toBe(true)
    expect(result.slice(2).every(i => i.done)).toBe(true)
  })

  it('불변성 — 입력 배열을 변형하지 않는다', () => {
    const input = [item('a', 100), item('b', 300), item('c', 200)]
    const inputCopy = [...input]
    const result = sortMemos(input)
    expect(result).not.toBe(input)
    expect(input).toEqual(inputCopy)
    expect(input).toHaveLength(3)
  })
})
