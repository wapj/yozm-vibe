import type { Session } from '../types'

const TYPE_LABEL: Record<Session['type'], string> = {
  focus: '집중',
  shortBreak: '짧은 휴식',
  longBreak: '긴 휴식',
}

interface TimerAlertProps {
  session: Session
  onDismiss: () => void
}

export function TimerAlert({ session, onDismiss }: TimerAlertProps) {
  return (
    <div className="timer-alert" role="alert">
      <span>{TYPE_LABEL[session.type]} 타이머가 종료되었습니다.</span>
      <button type="button" className="timer-alert__dismiss" onClick={onDismiss}>
        닫기
      </button>
    </div>
  )
}
