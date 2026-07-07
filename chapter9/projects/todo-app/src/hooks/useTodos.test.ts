import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { STORAGE_KEY } from '../constants'
import type { StorageData } from '../types'
import { useTodos } from './useTodos'

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

function readStoredTodos(): StorageData['todos'] {
  const raw = localStorage.getItem(STORAGE_KEY)
  return raw ? (JSON.parse(raw) as StorageData).todos : []
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useTodos', () => {
  it('add 호출 시 tags:[], done:false, ISO8601 createdAt으로 초기화된 할일이 상태에 반영된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })

    expect(result.current.todos).toHaveLength(1)
    const todo = result.current.todos[0]
    expect(todo.title).toBe('우유 사기')
    expect(todo.tags).toEqual([])
    expect(todo.done).toBe(false)
    expect(todo.id).toEqual(expect.any(String))
    expect(todo.createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/)
  })

  it('add 호출은 saveData를 경유해 localStorage에 실제로 반영된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })

    const stored = readStoredTodos()
    expect(stored).toHaveLength(1)
    expect(stored[0]).toMatchObject({ title: '우유 사기', tags: [], done: false })
  })

  it('toggleDone 호출은 localStorage에도 반영된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })
    const id = result.current.todos[0].id

    act(() => {
      result.current.toggleDone(id)
    })

    expect(result.current.todos[0].done).toBe(true)
    expect(readStoredTodos()[0].done).toBe(true)
  })

  it('remove 호출은 localStorage에서도 제거된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })
    const id = result.current.todos[0].id

    act(() => {
      result.current.remove(id)
    })

    expect(result.current.todos).toHaveLength(0)
    expect(readStoredTodos()).toHaveLength(0)
  })

  it('addTag 호출 시 태그가 추가되고 localStorage에도 반영된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })
    const id = result.current.todos[0].id

    act(() => {
      result.current.addTag(id, '집중')
    })

    expect(result.current.todos[0].tags).toEqual(['집중'])
    expect(readStoredTodos()[0].tags).toEqual(['집중'])
  })

  it('removeTag 호출 시 태그가 제거되고 localStorage에도 반영된다', () => {
    const { result } = renderHook(() => useTodos())

    act(() => {
      result.current.add('우유 사기')
    })
    const id = result.current.todos[0].id
    act(() => {
      result.current.addTag(id, '집중')
    })

    act(() => {
      result.current.removeTag(id, '집중')
    })

    expect(result.current.todos[0].tags).toEqual([])
    expect(readStoredTodos()[0].tags).toEqual([])
  })
})
