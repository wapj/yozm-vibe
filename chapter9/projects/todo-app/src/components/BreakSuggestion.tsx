import { durationForType } from '../lib/timer'
import type { SessionType } from '../types'

type BreakType = Extract<SessionType, 'shortBreak' | 'longBreak'>

const BREAK_LABEL: Record<BreakType, string> = {
  shortBreak: '짧은 휴식',
  longBreak: '긴 휴식',
}

interface BreakSuggestionProps {
  breakType: BreakType
  onStart: () => void
  onSkip: () => void
}

export function BreakSuggestion({ breakType, onStart, onSkip }: BreakSuggestionProps) {
  const minutes = Math.floor(durationForType(breakType) / (60 * 1000))

  return (
    <div className="break-suggestion" role="status">
      <span>
        {BREAK_LABEL[breakType]}({minutes}분)을 시작할까요?
      </span>
      <div className="break-suggestion__actions">
        <button type="button" className="break-suggestion__start" onClick={onStart}>
          휴식 시작
        </button>
        <button type="button" className="break-suggestion__skip" onClick={onSkip}>
          건너뛰기
        </button>
      </div>
    </div>
  )
}
