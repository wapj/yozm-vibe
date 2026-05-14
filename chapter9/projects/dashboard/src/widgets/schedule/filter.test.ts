import { describe, it, expect } from 'vitest'
import { formatToday, filterToday, sortByTime } from './filter'
import type { ScheduleItem } from './types'

function makeItem(overrides: Partial<ScheduleItem>): ScheduleItem {
  return {
    id: '1',
    date: '2026-05-06',
    time: null,
    title: 'test',
    done: false,
    ...overrides,
  }
}

describe('formatToday', () => {
  it('기본 — 2026-05-06 반환', () => {
    const d = new Date(2026, 4, 6) // month is 0-based
    expect(formatToday(d)).toBe('2026-05-06')
  })

  it('한 자리 월/일 zero-pad', () => {
    const d = new Date(2026, 0, 9) // Jan 9
    expect(formatToday(d)).toBe('2026-01-09')
  })
})

describe('filterToday', () => {
  it('기본 — 오늘 1개만 반환', () => {
    const items: ScheduleItem[] = [
      makeItem({ id: '1', date: '2026-05-06' }),
      makeItem({ id: '2', date: '2026-05-05' }),
      makeItem({ id: '3', date: '2026-05-07' }),
    ]
    const result = filterToday(items, '2026-05-06')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('1')
  })

  it('빈 배열 입력 → 빈 배열 반환', () => {
    expect(filterToday([], '2026-05-06')).toEqual([])
  })
})

describe('sortByTime', () => {
  it('시각 오름차순 정렬', () => {
    const items: ScheduleItem[] = [
      makeItem({ id: '1', time: '09:00' }),
      makeItem({ id: '2', time: '08:30' }),
      makeItem({ id: '3', time: '12:00' }),
    ]
    const result = sortByTime(items)
    expect(result.map(i => i.time)).toEqual(['08:30', '09:00', '12:00'])
  })

  it('time null 처리 — 시각 있음이 앞, null이 뒤', () => {
    const items: ScheduleItem[] = [
      makeItem({ id: '1', time: null }),
      makeItem({ id: '2', time: '10:00' }),
      makeItem({ id: '3', time: null }),
      makeItem({ id: '4', time: '08:00' }),
    ]
    const result = sortByTime(items)
    expect(result.map(i => i.time)).toEqual(['08:00', '10:00', null, null])
  })

  it('불변성 — 입력 배열 참조와 다른 배열 반환', () => {
    const items: ScheduleItem[] = [
      makeItem({ id: '1', time: '09:00' }),
      makeItem({ id: '2', time: '08:00' }),
    ]
    const original = [...items]
    const result = sortByTime(items)
    expect(result).not.toBe(items)
    expect(items).toHaveLength(original.length)
    expect(items[0].id).toBe(original[0].id)
  })
})
