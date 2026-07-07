export interface Todo {
  id: string
  title: string
  tags: string[]
  done: boolean
  createdAt: string
}

export type SessionType = 'focus' | 'shortBreak' | 'longBreak'
export type SessionResult = 'completed' | 'aborted'

export interface Session {
  id: string
  todoId: string
  type: SessionType
  startedAt: string
  endedAt: string
  result: SessionResult
}

export interface TimerState {
  todoId: string
  type: SessionType
  startedAt: string
}

export interface StorageData {
  schemaVersion: number
  todos: Todo[]
  sessions: Session[]
  timerState: TimerState | null
}
