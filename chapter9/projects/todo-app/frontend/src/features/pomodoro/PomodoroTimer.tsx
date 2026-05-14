import { useEffect, useRef } from "react";
import { type PomodoroSession } from "../../api/pomodoros";
import { useNow } from "../../hooks/useTimer";

type Props = {
  session: PomodoroSession;
  onExpire?: () => void;
};

export default function PomodoroTimer({ session, onExpire }: Props) {
  const now = useNow(1000);
  const firedRef = useRef(false);
  const startedAtMs = Date.parse(session.started_at);
  const elapsedSec = Math.max(0, Math.floor((now - startedAtMs) / 1000));
  const remainingSec = Math.max(0, session.planned_duration_sec - elapsedSec);
  const progressPercent = Math.min(100, Math.floor((elapsedSec / session.planned_duration_sec) * 100));

  useEffect(() => {
    if (remainingSec <= 0 && !firedRef.current && onExpire) {
      firedRef.current = true;
      onExpire();
    }
  }, [remainingSec, onExpire]);

  const mm = String(Math.floor(remainingSec / 60)).padStart(2, "0");
  const ss = String(remainingSec % 60).padStart(2, "0");

  return (
    <div data-testid="pomodoro-timer">
      <span data-testid="pomodoro-time">{mm}:{ss}</span>
      <progress data-testid="pomodoro-progress" value={progressPercent} max={100} />
    </div>
  );
}
