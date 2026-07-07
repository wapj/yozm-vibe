import { countCompletedPomodoros } from '../lib/sessions'
import type { Session, Todo } from '../types'
import { TodoItem } from './TodoItem'

interface TodoListProps {
  todos: Todo[]
  onToggle: (id: string) => void
  onRemove: (id: string) => void
  onUpdateTitle: (id: string, title: string) => void
  onAddTag: (id: string, tag: string) => void
  onRemoveTag: (id: string, tag: string) => void
  activeTodoId: string | null
  remainingLabel: string | null
  onStartFocus: (id: string) => void
  onStopFocus: () => void
  sessions: Session[]
}

export function TodoList({
  todos,
  onToggle,
  onRemove,
  onUpdateTitle,
  onAddTag,
  onRemoveTag,
  activeTodoId,
  remainingLabel,
  onStartFocus,
  onStopFocus,
  sessions,
}: TodoListProps) {
  if (todos.length === 0) {
    return <p className="todo-list__empty">할일이 없습니다.</p>
  }

  return (
    <ul className="todo-list">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggle}
          onRemove={onRemove}
          onUpdateTitle={onUpdateTitle}
          onAddTag={onAddTag}
          onRemoveTag={onRemoveTag}
          isFocusing={todo.id === activeTodoId}
          remainingLabel={todo.id === activeTodoId ? remainingLabel : null}
          onStartFocus={onStartFocus}
          onStopFocus={onStopFocus}
          completedCount={countCompletedPomodoros(sessions, todo.id)}
        />
      ))}
    </ul>
  )
}
