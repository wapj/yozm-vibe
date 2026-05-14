import type { TaskFilters } from "../../api/tasks";

type Props = {
  filters: TaskFilters;
  onChange: (next: TaskFilters) => void;
};

export default function TaskFilters({ filters, onChange }: Props) {
  const tagsValue = filters.tags ? filters.tags.join(", ") : "";

  function handleTagsChange(raw: string) {
    const parsed = raw
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    onChange({ ...filters, tags: parsed });
  }

  return (
    <div>
      <input
        type="search"
        data-testid="filter-q"
        placeholder="제목·메모 검색"
        value={filters.q ?? ""}
        onChange={(e) => onChange({ ...filters, q: e.target.value })}
      />
      <input
        type="text"
        data-testid="filter-tags"
        placeholder="태그(쉼표 구분)"
        value={tagsValue}
        onChange={(e) => handleTagsChange(e.target.value)}
      />
      <select
        data-testid="filter-date-preset"
        value={filters.date_preset ?? "all"}
        onChange={(e) =>
          onChange({
            ...filters,
            date_preset: e.target.value as TaskFilters["date_preset"],
          })
        }
      >
        <option value="all">전체</option>
        <option value="today">오늘</option>
        <option value="this_week">이번 주</option>
      </select>
    </div>
  );
}
