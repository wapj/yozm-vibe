import type { Task, UpdateTaskInput } from "../../api/tasks";
import TaskItem from "./TaskItem";

type Props = {
  tasks: Task[];
  onToggleStatus: (task: Task) => void;
  onDelete: (task: Task) => void;
  onSaveEdit: (task: Task, input: UpdateTaskInput) => Promise<void> | void;
  onStartPomodoro: (task: Task) => void;
};

export default function TaskList({ tasks, onToggleStatus, onDelete, onSaveEdit, onStartPomodoro }: Props) {
  if (tasks.length === 0) {
    return <p data-testid="task-empty">할일이 없습니다</p>;
  }

  return (
    <ul>
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onToggleStatus={onToggleStatus}
          onDelete={onDelete}
          onSaveEdit={onSaveEdit}
          onStartPomodoro={onStartPomodoro}
        />
      ))}
    </ul>
  );
}
