import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Todo } from '../types'
import { TodoItem } from './TodoItem'

function sampleTodo(overrides: Partial<Todo> = {}): Todo {
  return {
    id: 't1',
    title: '우유 사기',
    tags: [],
    done: false,
    createdAt: '2026-07-01T00:00:00.000Z',
    ...overrides,
  }
}

describe('TodoItem', () => {
  it('체크박스를 클릭하면 onToggle이 해당 id로 호출된다', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={onToggle}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.click(screen.getByRole('checkbox'))

    expect(onToggle).toHaveBeenCalledWith('t1')
  })

  it('완료된 항목은 체크박스가 checked 상태다', () => {
    render(
      <TodoItem
        todo={sampleTodo({ done: true })}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    expect(screen.getByRole('checkbox')).toBeChecked()
  })

  it('삭제 버튼을 클릭하면 onRemove가 해당 id로 호출된다', async () => {
    const user = userEvent.setup()
    const onRemove = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={onRemove}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.click(screen.getByRole('button', { name: '삭제' }))

    expect(onRemove).toHaveBeenCalledWith('t1')
  })

  it('제목을 더블클릭해 수정하고 Enter를 누르면 onUpdateTitle이 호출된다', async () => {
    const user = userEvent.setup()
    const onUpdateTitle = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={onUpdateTitle}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.dblClick(screen.getByText('우유 사기'))
    const input = screen.getByDisplayValue('우유 사기')
    await user.clear(input)
    await user.type(input, '빵 사기{Enter}')

    expect(onUpdateTitle).toHaveBeenCalledWith('t1', '빵 사기')
  })

  it('Escape를 누르면 편집을 취소하고 원래 제목을 유지한다', async () => {
    const user = userEvent.setup()
    const onUpdateTitle = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={onUpdateTitle}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.dblClick(screen.getByText('우유 사기'))
    const input = screen.getByDisplayValue('우유 사기')
    await user.clear(input)
    await user.type(input, '빵 사기')
    await user.keyboard('{Escape}')

    expect(onUpdateTitle).not.toHaveBeenCalled()
    expect(screen.getByText('우유 사기')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('빵 사기')).not.toBeInTheDocument()
  })

  it('입력창에서 포커스를 벗어나면(blur) 변경된 제목을 커밋한다', async () => {
    const user = userEvent.setup()
    const onUpdateTitle = vi.fn()
    render(
      <>
        <TodoItem
          todo={sampleTodo()}
          onToggle={vi.fn()}
          onRemove={vi.fn()}
          onUpdateTitle={onUpdateTitle}
          onAddTag={vi.fn()}
          onRemoveTag={vi.fn()}
          isFocusing={false}
          remainingLabel={null}
          onStartFocus={vi.fn()}
          onStopFocus={vi.fn()}
          completedCount={0}
        />
        <button type="button">바깥 요소</button>
      </>,
    )

    await user.dblClick(screen.getByText('우유 사기'))
    const input = screen.getByDisplayValue('우유 사기')
    await user.clear(input)
    await user.type(input, '빵 사기')
    await user.click(screen.getByRole('button', { name: '바깥 요소' }))

    expect(onUpdateTitle).toHaveBeenCalledWith('t1', '빵 사기')
  })

  it('제목을 변경하지 않고 커밋하면 onUpdateTitle이 호출되지 않는다', async () => {
    const user = userEvent.setup()
    const onUpdateTitle = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={onUpdateTitle}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.dblClick(screen.getByText('우유 사기'))
    await user.type(screen.getByDisplayValue('우유 사기'), '{Enter}')

    expect(onUpdateTitle).not.toHaveBeenCalled()
  })

  it('빈 제목으로 커밋하면 onUpdateTitle이 호출되지 않는다', async () => {
    const user = userEvent.setup()
    const onUpdateTitle = vi.fn()
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={onUpdateTitle}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.dblClick(screen.getByText('우유 사기'))
    const input = screen.getByDisplayValue('우유 사기')
    await user.clear(input)
    await user.type(input, '{Enter}')

    expect(onUpdateTitle).not.toHaveBeenCalled()
    expect(screen.getByText('우유 사기')).toBeInTheDocument()
  })

  it('태그 입력으로 부착하면 onAddTag가 호출되고, 갱신된 todo를 반영하면 태그가 화면에 나타난다', async () => {
    const user = userEvent.setup()
    const onAddTag = vi.fn()
    const { rerender } = render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={onAddTag}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.type(screen.getByLabelText('태그 추가'), '집중{Enter}')

    expect(onAddTag).toHaveBeenCalledWith('t1', '집중')

    rerender(
      <TodoItem
        todo={sampleTodo({ tags: ['집중'] })}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={onAddTag}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    expect(screen.getByText('집중')).toBeInTheDocument()
  })

  it('태그 제거 버튼을 클릭하면 onRemoveTag가 호출되고, 갱신된 todo를 반영하면 태그가 화면에서 사라진다', async () => {
    const user = userEvent.setup()
    const onRemoveTag = vi.fn()
    const { rerender } = render(
      <TodoItem
        todo={sampleTodo({ tags: ['집중'] })}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={onRemoveTag}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    await user.click(screen.getByRole('button', { name: '집중 태그 제거' }))

    expect(onRemoveTag).toHaveBeenCalledWith('t1', '집중')

    rerender(
      <TodoItem
        todo={sampleTodo({ tags: [] })}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={onRemoveTag}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={0}
      />,
    )

    expect(screen.queryByText('집중')).not.toBeInTheDocument()
  })

  it('완료된 뽀모도로 횟수를 표시한다', () => {
    render(
      <TodoItem
        todo={sampleTodo()}
        onToggle={vi.fn()}
        onRemove={vi.fn()}
        onUpdateTitle={vi.fn()}
        onAddTag={vi.fn()}
        onRemoveTag={vi.fn()}
        isFocusing={false}
        remainingLabel={null}
        onStartFocus={vi.fn()}
        onStopFocus={vi.fn()}
        completedCount={3}
      />,
    )

    expect(screen.getByText('완료 3회')).toBeInTheDocument()
  })
})
