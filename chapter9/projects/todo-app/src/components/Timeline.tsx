import { sortSessionsByStartedAtDesc } from '../lib/sessions'
import type { Session, Todo } from '../types'

const TYPE_LABEL: Record<Session['type'], string> = {
  focus: '집중',
  shortBreak: '짧은 휴식',
  longBreak: '긴 휴식',
}

const RESULT_LABEL: Record<Session['result'], string> = {
  completed: '완료',
  aborted: '중단',
}

const DELETED_TODO_LABEL = '(삭제된 할일)'

function formatClock(iso: string): string {
  const date = new Date(iso)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

interface TimelineProps {
  sessions: Session[]
  todos: Todo[]
}

export function Timeline({ sessions, todos }: TimelineProps) {
  const sorted = sortSessionsByStartedAtDesc(sessions)

  if (sorted.length === 0) {
    return <p className="timeline__empty">기록된 세션이 없습니다.</p>
  }

  const titleById = new Map(todos.map((todo) => [todo.id, todo.title]))

  return (
    <ul className="timeline">
      {sorted.map((session) => (
        <li key={session.id} className="timeline__item">
          <span className="timeline__time">
            {formatClock(session.startedAt)}–{formatClock(session.endedAt)}
          </span>
          <span className="timeline__title">{titleById.get(session.todoId) ?? DELETED_TODO_LABEL}</span>
          <span className="timeline__type">{TYPE_LABEL[session.type]}</span>
          <span className={`timeline__result timeline__result--${session.result}`}>
            {RESULT_LABEL[session.result]}
          </span>
        </li>
      ))}
    </ul>
  )
}
