import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TagFilter } from './TagFilter'

describe('TagFilter', () => {
  it('전달된 태그를 모두 버튼으로 렌더링한다', () => {
    render(<TagFilter tags={['급함', '집중']} selectedTags={[]} onToggle={vi.fn()} />)

    expect(screen.getByRole('button', { name: '급함' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '집중' })).toBeInTheDocument()
  })

  it('선택된 태그는 aria-pressed가 true다', () => {
    render(<TagFilter tags={['급함', '집중']} selectedTags={['집중']} onToggle={vi.fn()} />)

    expect(screen.getByRole('button', { name: '집중' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '급함' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('태그를 클릭하면 onToggle이 해당 태그로 호출된다', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    render(<TagFilter tags={['집중']} selectedTags={[]} onToggle={onToggle} />)

    await user.click(screen.getByRole('button', { name: '집중' }))

    expect(onToggle).toHaveBeenCalledWith('집중')
  })

  it('태그가 없으면 아무것도 렌더링하지 않는다', () => {
    const { container } = render(<TagFilter tags={[]} selectedTags={[]} onToggle={vi.fn()} />)

    expect(container).toBeEmptyDOMElement()
  })
})
