export type Task = {
  id: number;
  title: string;
  note: string | null;
  priority: "high" | "normal" | "low";
  status: "active" | "done";
  tags: string[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

export type TaskFilters = {
  q?: string;
  tags?: string[];
  date_preset?: "today" | "this_week" | "all";
  status?: "active" | "done";
};

export type CreateTaskInput = {
  title: string;
  note?: string | null;
  priority?: "high" | "normal" | "low";
  tags?: string[];
};

export async function listTasks(filters?: TaskFilters): Promise<Task[]> {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.q && filters.q.trim()) params.set("q", filters.q.trim());
    if (filters.tags && filters.tags.length > 0) {
      for (const t of filters.tags) {
        if (t.trim()) params.append("tags", t);
      }
    }
    if (filters.date_preset && filters.date_preset !== "all") {
      params.set("date_preset", filters.date_preset);
    }
    if (filters.status) params.set("status", filters.status);
  }
  const qs = params.toString();
  const url = qs ? `/api/tasks?${qs}` : "/api/tasks";
  const res = await fetch(url);
  if (!res.ok) throw new Error("failed to load tasks");
  return (await res.json()) as Task[];
}

export type UpdateTaskInput = {
  title?: string;
  note?: string | null;
  priority?: "high" | "normal" | "low";
  status?: "active" | "done";
  tags?: string[];
};

export async function createTask(input: CreateTaskInput): Promise<Task> {
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error("failed to create task");
  return (await res.json()) as Task;
}

export async function updateTask(id: number, input: UpdateTaskInput): Promise<Task> {
  const res = await fetch(`/api/tasks/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error("failed to update task");
  return (await res.json()) as Task;
}

export async function deleteTask(id: number): Promise<void> {
  const res = await fetch(`/api/tasks/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("failed to delete task");
}
