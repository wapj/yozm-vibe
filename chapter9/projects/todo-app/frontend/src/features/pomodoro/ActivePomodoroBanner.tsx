import { type PomodoroSession } from "../../api/pomodoros";
import PomodoroTimer from "./PomodoroTimer";

type Props = {
  active: PomodoroSession | null;
  onExpire?: () => void;
};

export default function ActivePomodoroBanner({ active, onExpire }: Props) {
  if (active === null) return null;
  return (
    <div data-testid="active-pomodoro-banner">
      활성 세션 #{active.id} task={active.task_id} phase={active.phase}
      <PomodoroTimer key={active.id} session={active} onExpire={onExpire} />
    </div>
  );
}
