import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import TaskFilters from "../src/features/tasks/TaskFilters";
import type { TaskFilters as TF } from "../src/api/tasks";

const base: TF = { status: "active" };

describe("TaskFilters", () => {
  it("검색바 입력 → onChange가 { ...filters, q: 'abc' }로 호출된다", () => {
    const onChange = vi.fn();
    render(<TaskFilters filters={base} onChange={onChange} />);

    fireEvent.change(screen.getByTestId("filter-q"), { target: { value: "abc" } });

    const last = onChange.mock.calls.at(-1)![0] as TF;
    expect(last.q).toBe("abc");
    expect(last.status).toBe("active");
  });

  it("태그 입력 'a, b ,c' → onChange가 tags: ['a','b','c']로 호출된다", () => {
    const onChange = vi.fn();
    render(<TaskFilters filters={base} onChange={onChange} />);

    fireEvent.change(screen.getByTestId("filter-tags"), { target: { value: "a, b ,c" } });

    const last = onChange.mock.calls.at(-1)![0] as TF;
    expect(last.tags).toEqual(["a", "b", "c"]);
  });

  it("태그 입력 비움 → onChange가 tags: []로 호출된다", () => {
    const onChange = vi.fn();
    const filtersWithTags: TF = { ...base, tags: ["x"] };
    render(<TaskFilters filters={filtersWithTags} onChange={onChange} />);

    fireEvent.change(screen.getByTestId("filter-tags"), { target: { value: "" } });

    const last = onChange.mock.calls.at(-1)![0] as TF;
    expect(last.tags).toEqual([]);
  });

  it("날짜 프리셋 select 'today' 선택 → onChange가 date_preset: 'today'로 호출된다", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TaskFilters filters={base} onChange={onChange} />);

    await user.selectOptions(screen.getByTestId("filter-date-preset"), "today");

    const last = onChange.mock.calls.at(-1)![0] as TF;
    expect(last.date_preset).toBe("today");
  });

  it("초기 렌더 시 filters props 값이 입력에 그대로 반영된다(controlled 검증)", () => {
    const initial: TF = { q: "hello", tags: ["foo", "bar"], date_preset: "this_week", status: "active" };
    render(<TaskFilters filters={initial} onChange={vi.fn()} />);

    expect((screen.getByTestId("filter-q") as HTMLInputElement).value).toBe("hello");
    expect((screen.getByTestId("filter-tags") as HTMLInputElement).value).toBe("foo, bar");
    expect((screen.getByTestId("filter-date-preset") as HTMLSelectElement).value).toBe("this_week");
  });
});
