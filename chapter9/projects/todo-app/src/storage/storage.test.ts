import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { STORAGE_KEY } from '../constants'
import type { StorageData } from '../types'
import { createEmptyData, loadData, saveData } from './index'

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

// Node 22+의 전역 localStorage(webstorage) 구현이 jsdom보다 먼저 전역을
// 점유해 getItem/setItem을 지원하지 않는 경우가 있어, 테스트 전용 메모리
// 스토리지로 교체한다.
Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: new MemoryStorage(),
})

function sampleData(): StorageData {
  return {
    schemaVersion: 1,
    todos: [
      { id: 't1', title: '샘플 할일', tags: ['work'], done: false, createdAt: '2026-07-01T00:00:00.000Z' },
    ],
    sessions: [
      {
        id: 's1',
        todoId: 't1',
        type: 'focus',
        startedAt: '2026-07-01T00:00:00.000Z',
        endedAt: '2026-07-01T00:25:00.000Z',
        result: 'completed',
      },
    ],
    timerState: null,
  }
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('storage', () => {
  it('save 후 load 결과가 원본과 동일하다', () => {
    const original = sampleData()
    saveData(original)

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(false)
    expect(data).toEqual(original)
  })

  it('손상된 JSON 입력 시 빈 상태와 경고 플래그를 반환한다', () => {
    localStorage.setItem(STORAGE_KEY, '{ this is not valid json')

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('스키마 버전 필드가 save/load 왕복 후에도 보존된다', () => {
    const original = sampleData()
    original.schemaVersion = 2
    saveData(original)

    const { data } = loadData()

    expect(data.schemaVersion).toBe(2)
  })

  it('todos가 배열이 아니면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = { ...sampleData(), todos: 'not-an-array' }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('schemaVersion이 숫자가 아니면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = { ...sampleData(), schemaVersion: '1' }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('저장된 데이터가 없으면(빈 상태) 경고 플래그 없이 빈 데이터를 반환한다', () => {
    const { data, corrupted } = loadData()

    expect(corrupted).toBe(false)
    expect(data).toEqual(createEmptyData())
  })

  it('timerState가 배열이면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = { ...sampleData(), timerState: ['not-an-object'] }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('timerState에 todoId가 없으면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = { ...sampleData(), timerState: { type: 'focus', startedAt: '2026-07-01T00:00:00.000Z' } }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('timerState의 type이 유효한 SessionType이 아니면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = {
      ...sampleData(),
      timerState: { todoId: 't1', type: 'invalidType', startedAt: '2026-07-01T00:00:00.000Z' },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('timerState의 startedAt이 문자열이 아니면 빈 상태와 경고 플래그를 반환한다', () => {
    const invalid = { ...sampleData(), timerState: { todoId: 't1', type: 'focus', startedAt: 12345 } }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(invalid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(true)
    expect(data).toEqual(createEmptyData())
  })

  it('필드를 모두 갖춘 정상 timerState는 그대로 통과한다', () => {
    const valid = {
      ...sampleData(),
      timerState: { todoId: 't1', type: 'focus', startedAt: '2026-07-01T00:00:00.000Z' },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(valid))

    const { data, corrupted } = loadData()

    expect(corrupted).toBe(false)
    expect(data.timerState).toEqual(valid.timerState)
  })

  it('저장 중 예외가 발생하면 실패 플래그를 반환한다', () => {
    vi.spyOn(localStorage, 'setItem').mockImplementation(() => {
      throw new DOMException('QuotaExceededError')
    })

    const { ok } = saveData(sampleData())

    expect(ok).toBe(false)
  })
})
