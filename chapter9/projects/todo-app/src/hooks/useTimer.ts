import { useCallback, useEffect, useRef, useState } from 'react'
import { durationForType, isComplete } from '../lib/timer'
import { loadData, saveData } from '../storage'
import type { Session, SessionResult, SessionType, StorageData, TimerState } from '../types'

const TICK_INTERVAL_MS = 1000

function isValidSessionType(value: unknown): value is SessionType {
  return value === 'focus' || value === 'shortBreak' || value === 'longBreak'
}

function isValidTimerState(value: TimerState | null): value is TimerState {
  if (value === null) return false
  return (
    typeof value.todoId === 'string' &&
    isValidSessionType(value.type) &&
    typeof value.startedAt === 'string' &&
    !Number.isNaN(new Date(value.startedAt).getTime())
  )
}

function createSession(
  todoId: string,
  type: SessionType,
  startedAt: string,
  endedAt: string,
  result: SessionResult,
): Session {
  return { id: crypto.randomUUID(), todoId, type, startedAt, endedAt, result }
}

type Patch = Pick<StorageData, 'timerState' | 'sessions'>

export function useTimer() {
  const [timerState, setTimerState] = useState<TimerState | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [lastCompletedSession, setLastCompletedSession] = useState<Session | null>(null)
  const [saveFailed, setSaveFailed] = useState(false)
  const initialized = useRef(false)

  const persist = useCallback((update: (latest: StorageData) => Patch) => {
    const latest = loadData().data
    const patch = update(latest)
    const next: StorageData = { ...latest, ...patch }
    const result = saveData(next)
    setSaveFailed(!result.ok)
    setTimerState(next.timerState)
    setSessions(next.sessions)
  }, [])

  const completeTimer = useCallback(
    (state: TimerState, now: string) => {
      const session = createSession(state.todoId, state.type, state.startedAt, now, 'completed')
      persist((latest) => ({
        timerState: null,
        sessions: [...latest.sessions, session],
      }))
      setLastCompletedSession(session)
    },
    [persist],
  )

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    const latest = loadData().data
    setSessions(latest.sessions)

    const restored = latest.timerState
    if (restored === null) return

    if (!isValidTimerState(restored)) {
      persist((fresh) => ({ timerState: null, sessions: fresh.sessions }))
      return
    }

    const now = new Date().toISOString()
    if (isComplete(restored.startedAt, durationForType(restored.type), now)) {
      completeTimer(restored, now)
    } else {
      setTimerState(restored)
    }
  }, [completeTimer, persist])

  useEffect(() => {
    if (timerState === null) return
    const interval = setInterval(() => {
      const now = new Date().toISOString()
      if (isComplete(timerState.startedAt, durationForType(timerState.type), now)) {
        completeTimer(timerState, now)
      }
    }, TICK_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [timerState, completeTimer])

  const start = useCallback(
    (todoId: string, type: SessionType = 'focus') => {
      const now = new Date().toISOString()

      if (timerState !== null) {
        if (timerState.todoId === todoId) return
        const confirmed = window.confirm('진행 중인 타이머를 중단하고 새 타이머를 시작할까요?')
        if (!confirmed) return
        persist((latest) => ({
          timerState: { todoId, type, startedAt: now },
          sessions: [
            ...latest.sessions,
            createSession(timerState.todoId, timerState.type, timerState.startedAt, now, 'aborted'),
          ],
        }))
        return
      }

      persist((latest) => ({
        timerState: { todoId, type, startedAt: now },
        sessions: latest.sessions,
      }))
    },
    [timerState, persist],
  )

  const stop = useCallback(() => {
    if (timerState === null) return
    const now = new Date().toISOString()
    persist((latest) => ({
      timerState: null,
      sessions: [...latest.sessions, createSession(timerState.todoId, timerState.type, timerState.startedAt, now, 'aborted')],
    }))
  }, [timerState, persist])

  return { timerState, sessions, lastCompletedSession, saveFailed, start, stop }
}
