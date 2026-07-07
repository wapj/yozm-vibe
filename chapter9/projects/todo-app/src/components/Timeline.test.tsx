import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Session, Todo } from '../types'
import { Timeline } from './Timeline'

const TODO: Todo = { id: 't1', title: '우유 사기', tags: [], done: false, createdAt: '2026-07-01T00:00:00.000Z' }
const TODO2: Todo = { id: 't2', title: '보고서 작성', tags: [], done: false, createdAt: '2026-07-01T00:00:00.000Z' }

function formatClock(iso: string): string {
  const date = new Date(iso)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function makeSession(overrides: Partial<Session>): Session {
  return {
    id: crypto.randomUUID(),
    todoId: 't1',
    type: 'focus',
    startedAt: '2026-07-01T00:00:00.000Z',
    endedAt: '2026-07-01T00:25:00.000Z',
    result: 'completed',
    ...overrides,
  }
}

describe('Timeline', () => {
  it('세션이 없으면 안내 문구를 표시한다', () => {
    render(<Timeline sessions={[]} todos={[TODO]} />)

    expect(screen.getByText('기록된 세션이 없습니다.')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('완료 세션은 "완료"로, 중단 세션은 "중단"으로 표시된다', () => {
    const completed = makeSession({ id: 's1', result: 'completed' })
    const aborted = makeSession({ id: 's2', result: 'aborted' })
    render(<Timeline sessions={[completed, aborted]} todos={[TODO]} />)

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('완료')
    expect(items[1]).toHaveTextContent('중단')
  })

  it('대상 할일 제목과 시작/종료 시각, 타입을 렌더링한다', () => {
    const session = makeSession({ id: 's1', type: 'shortBreak' })
    render(<Timeline sessions={[session]} todos={[TODO]} />)

    const item = screen.getByRole('listitem')
    expect(item).toHaveTextContent('우유 사기')
    expect(item).toHaveTextContent('짧은 휴식')
    expect(item).toHaveTextContent(formatClock(session.startedAt))
    expect(item).toHaveTextContent(formatClock(session.endedAt))
  })

  it('시작 시각 최신순으로 정렬해 표시한다', () => {
    const oldest = makeSession({ id: 's1', todoId: 't1', startedAt: '2026-07-01T00:00:00.000Z' })
    const newest = makeSession({ id: 's2', todoId: 't2', startedAt: '2026-07-02T00:00:00.000Z' })
    render(<Timeline sessions={[oldest, newest]} todos={[TODO, TODO2]} />)

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('보고서 작성')
    expect(items[1]).toHaveTextContent('우유 사기')
  })

  it('삭제된 할일을 참조하는 세션은 폴백 라벨을 표시한다', () => {
    const session = makeSession({ id: 's1', todoId: 'ghost' })
    render(<Timeline sessions={[session]} todos={[TODO]} />)

    expect(screen.getByRole('listitem')).toHaveTextContent('(삭제된 할일)')
  })
})
