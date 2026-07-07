import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { BreakSuggestion } from './BreakSuggestion'

describe('BreakSuggestion', () => {
  it('짧은 휴식 제안 문구와 조작 버튼을 표시한다', () => {
    render(<BreakSuggestion breakType="shortBreak" onStart={() => {}} onSkip={() => {}} />)

    expect(screen.getByRole('status')).toHaveTextContent('짧은 휴식(5분)을 시작할까요?')
    expect(screen.getByRole('button', { name: '휴식 시작' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '건너뛰기' })).toBeInTheDocument()
  })

  it('긴 휴식 타입이면 긴 휴식 라벨을 표시한다', () => {
    render(<BreakSuggestion breakType="longBreak" onStart={() => {}} onSkip={() => {}} />)

    expect(screen.getByRole('status')).toHaveTextContent('긴 휴식(15분)을 시작할까요?')
  })

  it('휴식 시작 버튼을 클릭하면 onStart가 호출된다', () => {
    const onStart = vi.fn()
    render(<BreakSuggestion breakType="shortBreak" onStart={onStart} onSkip={() => {}} />)

    fireEvent.click(screen.getByRole('button', { name: '휴식 시작' }))

    expect(onStart).toHaveBeenCalledTimes(1)
  })

  it('건너뛰기 버튼을 클릭하면 onSkip이 호출된다', () => {
    const onSkip = vi.fn()
    render(<BreakSuggestion breakType="shortBreak" onStart={() => {}} onSkip={onSkip} />)

    fireEvent.click(screen.getByRole('button', { name: '건너뛰기' }))

    expect(onSkip).toHaveBeenCalledTimes(1)
  })
})
