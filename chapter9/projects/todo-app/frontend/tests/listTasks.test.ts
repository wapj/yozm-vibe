import { describe, it, expect, vi, afterEach } from "vitest";
import { listTasks } from "../src/api/tasks";

describe("listTasks URL builder", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function setupFetchMock() {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal("fetch", fetchMock);
    return { getUrl: () => (fetchMock.mock.calls[0] as [string])[0] };
  }

  it("파라미터 없음 → /api/tasks", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks();
    expect(getUrl()).toBe("/api/tasks");
  });

  it("{ status: 'active' } → /api/tasks?status=active", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ status: "active" });
    expect(getUrl()).toBe("/api/tasks?status=active");
  });

  it("{ tags: ['a', 'b'] } → /api/tasks?tags=a&tags=b", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ tags: ["a", "b"] });
    expect(getUrl()).toBe("/api/tasks?tags=a&tags=b");
  });

  it("빈 tags 배열은 skip된다", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ tags: [] });
    expect(getUrl()).toBe("/api/tasks");
  });

  it("date_preset 'all'은 skip된다", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ date_preset: "all" });
    expect(getUrl()).toBe("/api/tasks");
  });

  it("q가 공백만이면 skip된다", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ q: "   " });
    expect(getUrl()).toBe("/api/tasks");
  });

  it("전체 조합 — 각 키 포함 + 빈 값 skip", async () => {
    const { getUrl } = setupFetchMock();
    await listTasks({ q: "hello", tags: ["x"], date_preset: "today", status: "done" });
    const url = getUrl();
    expect(url).toContain("q=hello");
    expect(url).toContain("tags=x");
    expect(url).toContain("date_preset=today");
    expect(url).toContain("status=done");
  });
});
