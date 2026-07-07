import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FOCUS_DURATION_MS, SHORT_BREAK_DURATION_MS, STORAGE_KEY } from '../constants'
import { countCompletedPomodoros } from '../lib/sessions'
import { createEmptyData } from '../storage'
import type { StorageData } from '../types'
import { useTimer } from './useTimer'

class MemoryStorage {
  private store = new Map<string, string>()
  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null
  }
  setItem(key: string, value: string): void {
    this.store.set(key, value)
  }
  removeItem(key: string): void {
    this.store.delete(key)
  }
  clear(): void {
    this.store.clear()
  }
}

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: new MemoryStorage(),
})

function writeStorage(data: StorageData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

function readStorage(): StorageData {
  return JSON.parse(localStorage.getItem(STORAGE_KEY)!) as StorageData
}

const NOW = '2026-07-01T00:00:00.000Z'
const TICK_INTERVAL_FOR_TEST = 1000

beforeEach(() => {
  localStorage.clear()
  vi.useFakeTimers()
  vi.setSystemTime(new Date(NOW))
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

describe('useTimer', () => {
  it('할일 클릭 시 timerState를 설정하고 저장한다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })

    expect(result.current.timerState).toEqual({ todoId: 'todo-1', type: 'focus', startedAt: NOW })
    expect(readStorage().timerState).toEqual({ todoId: 'todo-1', type: 'focus', startedAt: NOW })
  })

  it('진행 중 다른 할일 클릭 시 confirm 승인하면 기존 타이머를 aborted로 기록하고 새 타이머를 시작한다', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })

    const later = '2026-07-01T00:10:00.000Z'
    vi.setSystemTime(new Date(later))
    act(() => {
      result.current.start('todo-2')
    })

    expect(result.current.timerState).toEqual({ todoId: 'todo-2', type: 'focus', startedAt: later })
    expect(result.current.sessions).toHaveLength(1)
    expect(result.current.sessions[0]).toMatchObject({
      todoId: 'todo-1',
      result: 'aborted',
      startedAt: NOW,
      endedAt: later,
    })
  })

  it('진행 중 다른 할일 클릭 시 confirm 취소하면 기존 타이머를 유지하고 새 타이머를 시작하지 않는다', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })
    act(() => {
      result.current.start('todo-2')
    })

    expect(result.current.timerState).toEqual({ todoId: 'todo-1', type: 'focus', startedAt: NOW })
    expect(result.current.sessions).toHaveLength(0)
  })

  it('경과가 집중 시간 이상이면 completed 세션을 기록하고 timerState를 정리한다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })
    act(() => {
      vi.setSystemTime(new Date(new Date(NOW).getTime() + FOCUS_DURATION_MS))
      vi.advanceTimersByTime(TICK_INTERVAL_FOR_TEST)
    })

    const endedAt = new Date(new Date(NOW).getTime() + FOCUS_DURATION_MS + TICK_INTERVAL_FOR_TEST).toISOString()
    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(1)
    expect(result.current.sessions[0]).toMatchObject({
      todoId: 'todo-1',
      type: 'focus',
      result: 'completed',
      startedAt: NOW,
      endedAt,
    })
    expect(readStorage().timerState).toBeNull()
  })

  it('중단(stop) 호출 시 시작/종료 시각·대상 할일과 함께 aborted 세션을 기록하고 카운트에 포함하지 않는다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })
    const stoppedAt = '2026-07-01T00:05:00.000Z'
    vi.setSystemTime(new Date(stoppedAt))
    act(() => {
      result.current.stop()
    })

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions[0]).toMatchObject({
      todoId: 'todo-1',
      result: 'aborted',
      startedAt: NOW,
      endedAt: stoppedAt,
    })
    expect(countCompletedPomodoros(result.current.sessions, 'todo-1')).toBe(0)
  })

  it('복원: 저장된 timerState가 유효 범위 내면 경과를 이어서 표시한다', () => {
    writeStorage({ ...createEmptyData(), timerState: { todoId: 'todo-1', type: 'focus', startedAt: NOW } })
    vi.setSystemTime(new Date(new Date(NOW).getTime() + 60_000))

    const { result } = renderHook(() => useTimer())

    expect(result.current.timerState).toEqual({ todoId: 'todo-1', type: 'focus', startedAt: NOW })
  })

  it('복원: 집중 시간(25분)을 이미 초과했으면 즉시 completed 처리한다', () => {
    writeStorage({ ...createEmptyData(), timerState: { todoId: 'todo-1', type: 'focus', startedAt: NOW } })
    vi.setSystemTime(new Date(new Date(NOW).getTime() + FOCUS_DURATION_MS + 60_000))

    const { result } = renderHook(() => useTimer())

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(1)
    expect(result.current.sessions[0]).toMatchObject({ todoId: 'todo-1', result: 'completed' })
  })

  it('복원: startedAt이 파싱 불가(NaN)면 timerState를 폐기하고 빈 상태로 시작한다', () => {
    writeStorage({
      ...createEmptyData(),
      timerState: { todoId: 'todo-1', type: 'focus', startedAt: 'not-a-date' },
    })

    const { result } = renderHook(() => useTimer())

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(0)
    expect(readStorage().timerState).toBeNull()
  })

  it('복원: timerState에 todoId가 없으면 폐기하고 빈 상태로 시작한다', () => {
    writeStorage({
      ...createEmptyData(),
      timerState: { type: 'focus', startedAt: NOW } as unknown as StorageData['timerState'],
    })

    const { result } = renderHook(() => useTimer())

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(0)
  })

  it('복원: timerState의 type이 유효한 SessionType이 아니면 폐기하고 빈 상태로 시작한다', () => {
    writeStorage({
      ...createEmptyData(),
      timerState: { todoId: 'todo-1', type: 'invalidType', startedAt: NOW } as unknown as StorageData['timerState'],
    })

    const { result } = renderHook(() => useTimer())

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(0)
  })

  it('countCompletedPomodoros는 completed focus 세션만 집계한다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1')
    })
    act(() => {
      vi.setSystemTime(new Date(new Date(NOW).getTime() + FOCUS_DURATION_MS))
      vi.advanceTimersByTime(TICK_INTERVAL_FOR_TEST)
    })

    expect(countCompletedPomodoros(result.current.sessions, 'todo-1')).toBe(1)
    expect(countCompletedPomodoros(result.current.sessions, 'todo-2')).toBe(0)
  })

  it('휴식 타이머(shortBreak) 시작 후 duration 경과 시 completed 세션을 기록한다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1', 'shortBreak')
    })

    expect(result.current.timerState).toEqual({ todoId: 'todo-1', type: 'shortBreak', startedAt: NOW })

    act(() => {
      vi.setSystemTime(new Date(new Date(NOW).getTime() + SHORT_BREAK_DURATION_MS))
      vi.advanceTimersByTime(TICK_INTERVAL_FOR_TEST)
    })

    expect(result.current.timerState).toBeNull()
    expect(result.current.sessions).toHaveLength(1)
    expect(result.current.sessions[0]).toMatchObject({ todoId: 'todo-1', type: 'shortBreak', result: 'completed' })
  })

  it('휴식 완료 세션은 completed로 기록되지만 completed 뽀모도로 카운트에는 포함되지 않는다', () => {
    const { result } = renderHook(() => useTimer())

    act(() => {
      result.current.start('todo-1', 'shortBreak')
    })
    act(() => {
      vi.setSystemTime(new Date(new Date(NOW).getTime() + SHORT_BREAK_DURATION_MS))
      vi.advanceTimersByTime(TICK_INTERVAL_FOR_TEST)
    })

    expect(countCompletedPomodoros(result.current.sessions, 'todo-1')).toBe(0)
  })
})
