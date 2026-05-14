export type PomodoroPhase = "focus" | "short_break" | "long_break";
export type PomodoroEndReason = "completed" | "abandoned" | "discarded";
export type PomodoroSession = {
  id: number;
  task_id: number;
  phase: PomodoroPhase;
  started_at: string;
  planned_duration_sec: number;
  ended_at: string | null;
  end_reason: PomodoroEndReason | null;
};
export type StartPomodoroInput = {
  task_id: number;
  phase: PomodoroPhase;
  planned_duration_sec: number;
};

export type PomodoroNextPhase = { phase: PomodoroPhase; planned_duration_sec: number };

export class PomodoroConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PomodoroConflictError";
  }
}

export async function startPomodoro(input: StartPomodoroInput): Promise<PomodoroSession> {
  const res = await fetch("/api/pomodoros", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (res.status === 409) throw new PomodoroConflictError("active session conflict");
  if (!res.ok) throw new Error("failed to start pomodoro");
  return (await res.json()) as PomodoroSession;
}

export async function getActivePomodoro(): Promise<PomodoroSession | null> {
  const res = await fetch("/api/pomodoros/active");
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("failed to load active pomodoro");
  return (await res.json()) as PomodoroSession;
}

export async function endPomodoro(id: number): Promise<PomodoroSession> {
  const res = await fetch(`/api/pomodoros/${id}/end`, { method: "POST" });
  if (!res.ok) throw new Error("failed to end pomodoro");
  return (await res.json()) as PomodoroSession;
}

export async function getNextPhase(): Promise<PomodoroNextPhase> {
  const res = await fetch("/api/pomodoros/next-phase");
  if (!res.ok) throw new Error("failed to load next phase");
  return (await res.json()) as PomodoroNextPhase;
}

export async function discardPomodoro(
  id: number,
  end_reason: "abandoned" | "discarded"
): Promise<PomodoroSession> {
  const res = await fetch(`/api/pomodoros/${id}/discard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ end_reason }),
  });
  if (!res.ok) throw new Error("failed to discard pomodoro");
  return (await res.json()) as PomodoroSession;
}
