import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Session } from '../types'
import { TimerAlert } from './TimerAlert'

const FOCUS_SESSION: Session = {
  id: 's1',
  todoId: 't1',
  type: 'focus',
  startedAt: '2026-07-01T00:00:00.000Z',
  endedAt: '2026-07-01T00:25:00.000Z',
  result: 'completed',
}

describe('TimerAlert', () => {
  it('타이머 종료 안내 문구를 표시한다', () => {
    render(<TimerAlert session={FOCUS_SESSION} onDismiss={() => {}} />)

    expect(screen.getByRole('alert')).toHaveTextContent('집중 타이머가 종료되었습니다.')
  })

  it('휴식 세션이면 휴식 타입 라벨을 표시한다', () => {
    render(<TimerAlert session={{ ...FOCUS_SESSION, type: 'shortBreak' }} onDismiss={() => {}} />)

    expect(screen.getByRole('alert')).toHaveTextContent('짧은 휴식 타이머가 종료되었습니다.')
  })

  it('닫기 버튼을 클릭하면 onDismiss가 호출된다', () => {
    const onDismiss = vi.fn()
    render(<TimerAlert session={FOCUS_SESSION} onDismiss={onDismiss} />)

    fireEvent.click(screen.getByRole('button', { name: '닫기' }))

    expect(onDismiss).toHaveBeenCalledTimes(1)
  })
})
