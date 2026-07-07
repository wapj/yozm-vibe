import { SCHEMA_VERSION, STORAGE_KEY } from '../constants'
import type { SessionType, StorageData, TimerState } from '../types'

export interface LoadResult {
  data: StorageData
  corrupted: boolean
}

export interface SaveResult {
  ok: boolean
}

export function createEmptyData(): StorageData {
  return {
    schemaVersion: SCHEMA_VERSION,
    todos: [],
    sessions: [],
    timerState: null,
  }
}

function isValidSessionType(value: unknown): value is SessionType {
  return value === 'focus' || value === 'shortBreak' || value === 'longBreak'
}

function isValidTimerStateShape(value: unknown): value is TimerState {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false
  const candidate = value as Record<string, unknown>
  return (
    typeof candidate.todoId === 'string' &&
    isValidSessionType(candidate.type) &&
    typeof candidate.startedAt === 'string'
  )
}

function isValidStorageData(value: unknown): value is StorageData {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as Record<string, unknown>
  return (
    typeof candidate.schemaVersion === 'number' &&
    Array.isArray(candidate.todos) &&
    Array.isArray(candidate.sessions) &&
    (candidate.timerState === null || isValidTimerStateShape(candidate.timerState))
  )
}

export function loadData(): LoadResult {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw === null) {
    return { data: createEmptyData(), corrupted: false }
  }

  try {
    const parsed = JSON.parse(raw)
    if (!isValidStorageData(parsed)) {
      return { data: createEmptyData(), corrupted: true }
    }
    return { data: parsed, corrupted: false }
  } catch {
    return { data: createEmptyData(), corrupted: true }
  }
}

export function saveData(data: StorageData): SaveResult {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    return { ok: true }
  } catch {
    return { ok: false }
  }
}
