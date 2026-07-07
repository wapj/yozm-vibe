import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Session, Todo } from '../types'
import { TodoList } from './TodoList'

function sampleTodos(): Todo[] {
  return [
    { id: 't1', title: '첫 번째', tags: [], done: false, createdAt: '2026-07-01T00:00:00.000Z' },
    { id: 't2', title: '두 번째', tags: [], done: true, createdAt: '2026-07-02T00:00:00.000Z' },
  ]
}

describe('TodoList', () => {
  it('todos를 생성 순서 그대로 렌더링한다', () => {
    render(
      <TodoList
        todos={sampleTodos()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        activeTodoId={null}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        sessions={[]}
      />,
    )

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('첫 번째')
    expect(items[1]).toHaveTextContent('두 번째')
  })

  it('todos가 비어 있으면 안내 문구를 표시한다', () => {
    render(
      <TodoList
        todos={[]}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        activeTodoId={null}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        sessions={[]}
      />,
    )

    expect(screen.getByText('할일이 없습니다.')).toBeInTheDocument()
  })

  it('할일별로 완료된 뽀모도로 횟수만 집계해 표시한다', () => {
    const sessions: Session[] = [
      { id: 's1', todoId: 't1', type: 'focus', startedAt: '', endedAt: '', result: 'completed' },
      { id: 's2', todoId: 't1', type: 'focus', startedAt: '', endedAt: '', result: 'aborted' },
      { id: 's3', todoId: 't2', type: 'focus', startedAt: '', endedAt: '', result: 'completed' },
      { id: 's4', todoId: 't2', type: 'focus', startedAt: '', endedAt: '', result: 'completed' },
    ]

    render(
      <TodoList
        todos={sampleTodos()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        activeTodoId={null}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        sessions={sessions}
      />,
    )

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('완료 1회')
    expect(items[1]).toHaveTextContent('완료 2회')
  })
})
