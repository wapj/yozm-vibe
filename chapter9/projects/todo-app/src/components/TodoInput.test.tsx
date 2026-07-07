import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TodoInput } from './TodoInput'

describe('TodoInput', () => {
  it('제목을 입력하고 추가 버튼을 클릭하면 onAdd가 트리밍된 제목으로 호출된다', async () => {
    const user = userEvent.setup()
    const onAdd = vi.fn()
    render(<TodoInput onAdd={onAdd} />)

    await user.type(screen.getByLabelText('새 할일'), '  우유 사기  ')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(onAdd).toHaveBeenCalledWith('우유 사기')
  })

  it('추가 후 입력창을 비운다', async () => {
    const user = userEvent.setup()
    render(<TodoInput onAdd={vi.fn()} />)

    const input = screen.getByLabelText('새 할일')
    await user.type(input, '할일')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(input).toHaveValue('')
  })

  it('빈 제목은 onAdd를 호출하지 않는다', async () => {
    const user = userEvent.setup()
    const onAdd = vi.fn()
    render(<TodoInput onAdd={onAdd} />)

    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(onAdd).not.toHaveBeenCalled()
  })
})
