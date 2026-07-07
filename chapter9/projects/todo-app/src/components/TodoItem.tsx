import { useState } from 'react'
import type { KeyboardEvent } from 'react'
import type { Todo } from '../types'

interface TodoItemProps {
  todo: Todo
  onToggle: (id: string) => void
  onRemove: (id: string) => void
  onUpdateTitle: (id: string, title: string) => void
  onAddTag: (id: string, tag: string) => void
  onRemoveTag: (id: string, tag: string) => void
  isFocusing: boolean
  remainingLabel: string | null
  onStartFocus: (id: string) => void
  onStopFocus: () => void
  completedCount: number
}

export function TodoItem({
  todo,
  onToggle,
  onRemove,
  onUpdateTitle,
  onAddTag,
  onRemoveTag,
  isFocusing,
  remainingLabel,
  onStartFocus,
  onStopFocus,
  completedCount,
}: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(todo.title)
  const [tagDraft, setTagDraft] = useState('')

  const startEdit = () => {
    setDraft(todo.title)
    setIsEditing(true)
  }

  const commitEdit = () => {
    const trimmed = draft.trim()
    if (trimmed.length > 0 && trimmed !== todo.title) {
      onUpdateTitle(todo.id, trimmed)
    }
    setIsEditing(false)
  }

  const cancelEdit = () => {
    setDraft(todo.title)
    setIsEditing(false)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') commitEdit()
    if (event.key === 'Escape') cancelEdit()
  }

  const commitTag = () => {
    const trimmed = tagDraft.trim()
    if (trimmed.length > 0) {
      onAddTag(todo.id, trimmed)
    }
    setTagDraft('')
  }

  const handleTagKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      commitTag()
    }
  }

  return (
    <li className={`todo-item${todo.done ? ' todo-item--done' : ''}`}>
      <input
        type="checkbox"
        className="todo-item__checkbox"
        checked={todo.done}
        onChange={() => onToggle(todo.id)}
        aria-label={`${todo.title} 완료`}
      />
      <div className="todo-item__body">
        {isEditing ? (
          <input
            type="text"
            className="todo-item__edit-input"
            value={draft}
            autoFocus
            onChange={(event) => setDraft(event.target.value)}
            onBlur={commitEdit}
            onKeyDown={handleKeyDown}
          />
        ) : (
          <span className="todo-item__title" onDoubleClick={startEdit}>
            {todo.title}
          </span>
        )}
        <span className="todo-item__completed-count">완료 {completedCount}회</span>
        <div className="todo-item__tags">
          {todo.tags.map((tag) => (
            <span key={tag} className="todo-item__tag">
              {tag}
              <button
                type="button"
                className="todo-item__tag-remove"
                aria-label={`${tag} 태그 제거`}
                onClick={() => onRemoveTag(todo.id, tag)}
              >
                ×
              </button>
            </span>
          ))}
          <input
            type="text"
            className="todo-item__tag-input"
            placeholder="태그 추가"
            aria-label="태그 추가"
            value={tagDraft}
            onChange={(event) => setTagDraft(event.target.value)}
            onKeyDown={handleTagKeyDown}
          />
        </div>
        <div className="todo-item__timer">
          {isFocusing ? (
            <>
              <span className="todo-item__remaining">{remainingLabel}</span>
              <button type="button" className="todo-item__stop-focus" onClick={onStopFocus}>
                중단
              </button>
            </>
          ) : (
            <button type="button" className="todo-item__start-focus" onClick={() => onStartFocus(todo.id)}>
              집중 시작
            </button>
          )}
        </div>
      </div>
      <button type="button" className="todo-item__delete" onClick={() => onRemove(todo.id)}>
        삭제
      </button>
    </li>
  )
}
