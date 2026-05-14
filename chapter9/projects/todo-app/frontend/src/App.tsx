import { useEffect, useRef, useState } from "react";
import { listTasks, updateTask, deleteTask, type Task, type TaskFilters, type UpdateTaskInput } from "./api/tasks";
import { getActivePomodoro, startPomodoro, endPomodoro, discardPomodoro, getNextPhase, PomodoroConflictError, type PomodoroSession } from "./api/pomodoros";
import TaskList from "./features/tasks/TaskList";
import TaskForm from "./features/tasks/TaskForm";
import TaskFilters from "./features/tasks/TaskFilters";
import ActivePomodoroBanner from "./features/pomodoro/ActivePomodoroBanner";
import PomodoroConflictDialog from "./features/pomodoro/PomodoroConflictDialog";
import { NextFocusPromptDialog } from "./features/pomodoro/NextFocusPromptDialog";
import { useNotification } from "./hooks/useNotification";
import { Toast } from "./components/Toast";

export default function App() {
  const { notify, requestPermission } = useNotification();
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFilters>({ status: "active" });
  const [activePomodoro, setActivePomodoro] = useState<PomodoroSession | null>(null);
  const [conflictSession, setConflictSession] = useState<PomodoroSession | null>(null);
  const [pendingStartTask, setPendingStartTask] = useState<Task | null>(null);
  const [nextFocusPromptTask, setNextFocusPromptTask] = useState<number | null>(null);
  const [toasts, setToasts] = useState<{ id: number; message: string }[]>([]);
  const toastIdRef = useRef(0);

  const showToast = (message: string) => {
    const id = ++toastIdRef.current;
    setToasts((prev) => [...prev, { id, message }]);
  };

  const removeToast = (id: number) => setToasts((prev) => prev.filter((t) => t.id !== id));

  useEffect(() => {
    setTasks(null);
    listTasks(filters)
      .then(setTasks)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [filters]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { requestPermission(); }, []);

  useEffect(() => {
    getActivePomodoro()
      .then(async (active) => {
        if (active && Date.parse(active.started_at) + active.planned_duration_sec * 1000 <= Date.now()) {
          const title = active.phase === "focus" ? "집중 세션이 종료되었습니다" : "휴식이 종료되었습니다";
          const body = `task #${active.task_id}`;
          notify(title, body, showToast);
          try {
            await endPomodoro(active.id);
          } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
          } finally {
            setActivePomodoro(null);
          }
        } else {
          setActivePomodoro(active);
        }
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleToggleStatus(task: Task) {
    try {
      const updated = await updateTask(task.id, {
        status: task.status === "active" ? "done" : "active",
      });
      setTasks((prev) => prev ? prev.map((t) => t.id === task.id ? updated : t) : prev);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleDelete(task: Task) {
    try {
      await deleteTask(task.id);
      setTasks((prev) => prev ? prev.filter((t) => t.id !== task.id) : prev);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleStartPomodoro(task: Task) {
    try {
      const session = await startPomodoro({ task_id: task.id, phase: "focus", planned_duration_sec: 1500 });
      setActivePomodoro(session);
    } catch (e: unknown) {
      if (e instanceof PomodoroConflictError) {
        try {
          const active = await getActivePomodoro();
          if (active) {
            setConflictSession(active);
            setPendingStartTask(task);
          } else {
            const session = await startPomodoro({ task_id: task.id, phase: "focus", planned_duration_sec: 1500 });
            setActivePomodoro(session);
          }
        } catch (inner) {
          setError(inner instanceof Error ? inner.message : String(inner));
          setConflictSession(null);
          setPendingStartTask(null);
        }
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    }
  }

  async function handlePomodoroExpire() {
    if (!activePomodoro) return;
    const expired = activePomodoro;
    const title = expired.phase === "focus" ? "집중 세션이 종료되었습니다" : "휴식이 종료되었습니다";
    const body = `task #${expired.task_id}`;
    notify(title, body, showToast);
    try {
      await endPomodoro(expired.id);
      if (expired.phase === "focus") {
        const next = await getNextPhase();
        if (next.phase === "short_break" || next.phase === "long_break") {
          const session = await startPomodoro({
            task_id: expired.task_id,
            phase: next.phase,
            planned_duration_sec: next.planned_duration_sec,
          });
          setActivePomodoro(session);
          return;
        }
      }
      setActivePomodoro(null);
      if (expired.phase !== "focus") {
        setNextFocusPromptTask(expired.task_id);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setActivePomodoro(null);
    }
  }

  async function handleConflictComplete() {
    if (!conflictSession || !pendingStartTask) return;
    try {
      await endPomodoro(conflictSession.id);
      const session = await startPomodoro({ task_id: pendingStartTask.id, phase: "focus", planned_duration_sec: 1500 });
      setActivePomodoro(session);
      setConflictSession(null);
      setPendingStartTask(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleConflictDiscard() {
    if (!conflictSession || !pendingStartTask) return;
    try {
      await discardPomodoro(conflictSession.id, "discarded");
      const session = await startPomodoro({ task_id: pendingStartTask.id, phase: "focus", planned_duration_sec: 1500 });
      setActivePomodoro(session);
      setConflictSession(null);
      setPendingStartTask(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function handleConflictCancel() {
    setConflictSession(null);
    setPendingStartTask(null);
  }

  async function handleNextFocusYes() {
    if (nextFocusPromptTask === null) return;
    const taskId = nextFocusPromptTask;
    try {
      const next = await getNextPhase();
      if (next.phase !== "focus") {
        setError("expected focus phase from next-phase API");
        return;
      }
      const session = await startPomodoro({
        task_id: taskId,
        phase: "focus",
        planned_duration_sec: next.planned_duration_sec,
      });
      setActivePomodoro(session);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setActivePomodoro(null);
    } finally {
      setNextFocusPromptTask(null);
    }
  }

  function handleNextFocusNo() {
    setNextFocusPromptTask(null);
  }

  async function handleSaveEdit(task: Task, input: UpdateTaskInput): Promise<void> {
    try {
      const updated = await updateTask(task.id, input);
      setTasks((prev) => prev ? prev.map((t) => t.id === task.id ? updated : t) : prev);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      throw e;
    }
  }

  return (
    <div>
      <h1>Todo + Pomodoro</h1>
      <ActivePomodoroBanner active={activePomodoro} onExpire={handlePomodoroExpire} />
      <TaskFilters filters={filters} onChange={setFilters} />
      <label>
        <input
          type="checkbox"
          data-testid="toggle-show-completed"
          checked={filters.status === undefined}
          onChange={(e) => {
            if (e.target.checked) {
              setFilters((f) => ({ ...f, status: undefined }));
            } else {
              setFilters((f) => ({ ...f, status: "active" }));
            }
          }}
        />
        {" "}완료된 항목 보기
      </label>
      <TaskForm onCreated={(task) => setTasks((prev) => prev ? [task, ...prev] : [task])} />
      {error && <p data-testid="task-error">Error: {error}</p>}
      {tasks === null && !error && <p data-testid="task-loading">로딩 중...</p>}
      {tasks !== null && (
        <TaskList
          tasks={tasks}
          onToggleStatus={handleToggleStatus}
          onDelete={handleDelete}
          onSaveEdit={handleSaveEdit}
          onStartPomodoro={handleStartPomodoro}
        />
      )}
      {conflictSession && pendingStartTask && (
        <PomodoroConflictDialog
          conflictSession={conflictSession}
          onComplete={handleConflictComplete}
          onDiscard={handleConflictDiscard}
          onCancel={handleConflictCancel}
        />
      )}
      {nextFocusPromptTask !== null && (
        <NextFocusPromptDialog
          taskId={nextFocusPromptTask}
          onYes={handleNextFocusYes}
          onNo={handleNextFocusNo}
        />
      )}
      <div
        data-testid="toast-container"
        style={{ position: "fixed", top: 16, right: 16, display: "flex", flexDirection: "column", gap: 8 }}
      >
        {toasts.map((t) => (
          <Toast key={t.id} message={t.message} onClose={() => removeToast(t.id)} />
        ))}
      </div>
    </div>
  );
}
