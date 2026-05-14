import type { MemoItem } from './types'

export function sortMemos(items: MemoItem[]): MemoItem[] {
  return [...items].sort((a, b) => {
    if (a.done !== b.done) return a.done ? 1 : -1
    return b.createdAt - a.createdAt
  })
}
