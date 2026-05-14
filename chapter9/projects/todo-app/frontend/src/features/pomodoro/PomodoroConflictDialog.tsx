import { type PomodoroSession } from "../../api/pomodoros";

type Props = {
  conflictSession: PomodoroSession;
  onComplete: () => void;
  onDiscard: () => void;
  onCancel: () => void;
};

export default function PomodoroConflictDialog({ conflictSession, onComplete, onDiscard, onCancel }: Props) {
  return (
    <div role="dialog" aria-modal="true" data-testid="pomodoro-conflict-dialog">
      <p>현재 활성 세션을 어떻게 할까요?</p>
      <p>세션 #{conflictSession.id} task={conflictSession.task_id} phase={conflictSession.phase}</p>
      <button data-testid="conflict-complete" onClick={onComplete}>완료</button>
      <button data-testid="conflict-discard" onClick={onDiscard}>폐기</button>
      <button data-testid="conflict-cancel" onClick={onCancel}>취소</button>
    </div>
  );
}
