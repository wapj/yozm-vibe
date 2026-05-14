import { useState } from "react";
import { createTask, type Task } from "../../api/tasks";

type Props = { onCreated: (task: Task) => void };

export default function TaskForm({ onCreated }: Props) {
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [priority, setPriority] = useState<"high" | "normal" | "low">("normal");
  const [tags, setTags] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    setSubmitting(true);
    setError(null);
    try {
      const task = await createTask({
        title: title.trim(),
        note: note || null,
        priority,
        tags: tagList,
      });
      onCreated(task);
      setTitle("");
      setNote("");
      setPriority("normal");
      setTags("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        data-testid="task-form-title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="제목"
        required
      />
      <textarea
        data-testid="task-form-note"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="메모"
      />
      <select
        data-testid="task-form-priority"
        value={priority}
        onChange={(e) => setPriority(e.target.value as "high" | "normal" | "low")}
      >
        <option value="high">high</option>
        <option value="normal">normal</option>
        <option value="low">low</option>
      </select>
      <input
        data-testid="task-form-tags"
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        placeholder="쉼표로 구분"
      />
      <button data-testid="task-form-submit" type="submit" disabled={submitting}>
        추가
      </button>
      {error && <p data-testid="task-form-error">{error}</p>}
    </form>
  );
}
