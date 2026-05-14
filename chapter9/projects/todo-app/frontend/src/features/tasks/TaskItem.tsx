import { useState } from "react";
import type { Task, UpdateTaskInput } from "../../api/tasks";

type Props = {
  task: Task;
  onToggleStatus: (task: Task) => void;
  onDelete: (task: Task) => void;
  onSaveEdit: (task: Task, input: UpdateTaskInput) => Promise<void> | void;
  onStartPomodoro: (task: Task) => void;
};

export default function TaskItem({ task, onToggleStatus, onDelete, onSaveEdit, onStartPomodoro }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [titleDraft, setTitleDraft] = useState(task.title);
  const [noteDraft, setNoteDraft] = useState(task.note ?? "");
  const [priorityDraft, setPriorityDraft] = useState<"high" | "normal" | "low">(task.priority);
  const [tagsDraft, setTagsDraft] = useState(task.tags.join(", "));

  function enterEdit() {
    setTitleDraft(task.title);
    setNoteDraft(task.note ?? "");
    setPriorityDraft(task.priority);
    setTagsDraft(task.tags.join(", "));
    setIsEditing(true);
  }

  async function handleSave() {
    if (!titleDraft.trim()) return;
    const tags = tagsDraft.split(",").map((s) => s.trim()).filter(Boolean);
    try {
      await onSaveEdit(task, {
        title: titleDraft,
        note: noteDraft === "" ? null : noteDraft,
        priority: priorityDraft,
        tags,
      });
      setIsEditing(false);
    } catch {
      // parent handles error display; stay in edit mode
    }
  }

  if (isEditing) {
    return (
      <li data-testid={`task-${task.id}`}>
        <input
          data-testid={`edit-title-${task.id}`}
          value={titleDraft}
          onChange={(e) => setTitleDraft(e.target.value)}
        />
        <input
          data-testid={`edit-note-${task.id}`}
          value={noteDraft}
          onChange={(e) => setNoteDraft(e.target.value)}
        />
        <select
          data-testid={`edit-priority-${task.id}`}
          value={priorityDraft}
          onChange={(e) => setPriorityDraft(e.target.value as "high" | "normal" | "low")}
        >
          <option value="high">high</option>
          <option value="normal">normal</option>
          <option value="low">low</option>
        </select>
        <input
          data-testid={`edit-tags-${task.id}`}
          value={tagsDraft}
          onChange={(e) => setTagsDraft(e.target.value)}
        />
        <button data-testid={`task-save-${task.id}`} onClick={handleSave}>저장</button>
        <button data-testid={`task-cancel-${task.id}`} onClick={() => setIsEditing(false)}>취소</button>
      </li>
    );
  }

  return (
    <li data-testid={`task-${task.id}`}>
      <strong>{task.title}</strong>
      <span> [{task.priority}]</span>
      <span> {task.status}</span>
      {task.tags.length > 0 && <span> {task.tags.join(", ")}</span>}
      <span> 🍅 ×0</span>
      <button
        data-testid={`task-toggle-${task.id}`}
        onClick={() => onToggleStatus(task)}
      >
        {task.status === "active" ? "완료" : "되돌리기"}
      </button>
      <button
        data-testid={`task-delete-${task.id}`}
        onClick={() => onDelete(task)}
      >
        삭제
      </button>
      <button
        data-testid={`task-edit-${task.id}`}
        onClick={enterEdit}
      >
        편집
      </button>
      <button
        data-testid={`task-start-${task.id}`}
        onClick={() => onStartPomodoro(task)}
      >
        시작
      </button>
    </li>
  );
}
